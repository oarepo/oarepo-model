#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Utility classes for handling lazy models."""

from __future__ import annotations

import abc
import copy
from collections.abc import Iterator, Mapping
from functools import cached_property
from typing import Any, override

import marshmallow

from oarepo_model.utils import deeply_copy_to_mutable, import_runtime_json


class LazyPythonMapping(Mapping, abc.ABC):
    """Lazily loads a mapping on the first access.

    To use it, subclass it and implement the `_load_data` method.
    """

    def __init__(self) -> None:
        """Initialize with the model name, keys and namespace file name to resolve."""
        self._data: dict[str, Any] = {}
        self._loaded = False

    @abc.abstractmethod
    def _load_data(self) -> dict[str, Any]:
        """Load the data from the namespace file."""
        raise NotImplementedError

    def _ensure(self) -> None:
        """Resolve the data on first use."""
        if self._loaded:
            return
        self._data = self._load_data()
        self._loaded = True

    def __getitem__(self, key: str) -> Any:
        """Get an item from the mapping, resolving it first."""
        self._ensure()
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        """Iterate over the mapping keys, resolving it first."""
        self._ensure()
        return iter(self._data)

    def __len__(self) -> int:
        """Get the number of items in the mapping, resolving it first."""
        self._ensure()
        return len(self._data)


class LazyJSONNamespaceFilePart(LazyPythonMapping, abc.ABC):
    """Lazily loads and exposes a JSON subtree(s) from a namespace file.

    To use it, subclass it and implement the `_get_path` and `_set_path` methods.
    """

    extra_fields: Mapping[str, Any] = {}

    def __init__(
        self, model: str, keys: list[str] | None, filename: str, initial_content: dict[str, Any] | None = None
    ) -> None:
        """Initialize with the model name, keys and namespace file name to resolve."""
        super().__init__()
        self._model = model
        self._keys = keys
        self._filename = filename
        self._initial_content = initial_content

    @abc.abstractmethod
    def _get_path(self, data: Any, path: str) -> dict[str, Any]:
        """Get the value at the given path in the data."""
        raise NotImplementedError

    @abc.abstractmethod
    def _set_path(self, data: Any, path: str, value: Any) -> None:
        """Set the value at the given path in the data."""
        raise NotImplementedError

    def _load_original_json(self) -> dict[str, Any]:
        """Load the original JSON content from the namespace file."""
        return import_runtime_json(self._model, self._filename)

    def _load_data(self) -> dict[str, Any]:
        """Load the data from the namespace file, resolving the keys if specified."""
        loaded = self._load_original_json()
        generated = deeply_copy_to_mutable(self._initial_content) if self._initial_content else {}
        for key in self._keys or []:
            value = self._get_path(loaded, key)
            self._set_path(generated, key, value)

        for fld, value in self.extra_fields.items():
            if fld not in generated:
                self._set_path(generated, fld, copy.deepcopy(value))

        return generated

    def __getitem__(self, key: str) -> Any:
        """Get an item from the mapping, resolving it first."""
        self._ensure()
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        """Iterate over the mapping keys, resolving it first."""
        self._ensure()
        return iter(self._data)

    def __len__(self) -> int:
        """Get the number of items in the mapping, resolving it first."""
        self._ensure()
        return len(self._data)


class LazyMarshmallowSchema(marshmallow.Schema):
    """A marshmallow schema that lazily builds and delegates to the real schema.

    A proxied schema is generated dynamically on the first `load`/`dump` call.
    """

    model: str
    keys: list[str] | None = None
    initial_schema: marshmallow.Schema | None = None

    @classmethod
    def _get_target_schema(cls) -> marshmallow.Schema:
        """Return an instance of the schema `keys` should be resolved against."""
        raise NotImplementedError

    @classmethod
    def _missing_field(cls, key: str) -> marshmallow.fields.Field:
        """Return a fallback field to use when `key` can not be resolved on the target schema.

        The default just fails loudly - a missing field is a genuine error for
        the "real" record schema. Subclasses (e.g. for the UI schema, where not
        every field necessarily has a UI-specific counterpart) may override this
        to return a fallback field instead.
        """
        raise KeyError(key)

    @cached_property
    def proxied_schema(self) -> marshmallow.Schema:
        """Build the real marshmallow schema class for `model`/`keys`.

        First builds a tree - key (without dot) -> the target model's real
        marshmallow field, or (for keys with more path segments left) a nested
        dict of the same shape - then turns that tree into actual marshmallow
        Schema classes.
        """
        target_schema = self._get_target_schema()

        # Step 1: descend into the target schema for each key, same as LazyMapping/
        # LazyJSONSchema do for the mapping/json schema, building a tree of
        # Field instances (leaves) and plain dicts (intermediate path segments).
        #
        # For example, keys "foo.bar" and "foo.baz" will generate
        # code like {"foo": {"bar": fld_bar, "baz": fld_baz}}
        tree: dict[str, Any] = {}
        for key in self.keys or []:
            field = None

            # if the field is in the initial schema, use it (overriden by the user);
            # otherwise, find it in the target schema
            if self.initial_schema:
                field = self._find_key_in_schema(key, self.initial_schema)
            if field is None:
                field = self._find_key_in_schema(key, target_schema)
            if field is None:
                field = self._missing_field(key)

            # set the field in the tree
            parts = key.split(".")
            dest = tree
            for part in parts[:-1]:
                dest = dest.setdefault(part, {})
            dest[parts[-1]] = field

        clz = self._build_schema_class(type(self).__name__, tree)
        return clz()

    def _find_key_in_schema(self, key: str, source_schema: marshmallow.Schema) -> marshmallow.fields.Field | None:
        """Find a field in a schema by key path."""
        parts = key.split(".")
        for part in parts[:-1]:
            if part not in source_schema.fields:
                return None
            field = source_schema.fields[part]
            if not isinstance(field, marshmallow.fields.Nested):
                raise TypeError(
                    f"Field {part!r} on the path to {key!r} is not a nested field.",
                )
            source_schema = field.schema
        if parts[-1] not in source_schema.fields:
            return None
        return source_schema.fields[parts[-1]]

    @classmethod
    def _build_schema_class(cls, name: str, node: dict[str, Any]) -> type[marshmallow.Schema]:
        """Turn a tree (key->field or subtree) into a Schema class.

        A nested dict becomes a Nested field pointing to a (recursively built)
        schema class; a leaf field is deep-copied, since a marshmallow Field
        instance can only ever be bound to a single schema class.
        """
        attrs: dict[str, Any] = {}
        for key, value in node.items():
            if isinstance(value, dict):
                attrs[key] = marshmallow.fields.Nested(cls._build_schema_class(f"{name}_{key}", value))
            else:
                attrs[key] = copy.deepcopy(value)

        class Meta:
            unknown = marshmallow.RAISE

        attrs["Meta"] = Meta
        return type(name, (marshmallow.Schema,), attrs)

    @override
    def load(self, *args: Any, **kwargs: Any) -> Any:
        """Load data using the lazily-resolved proxied schema."""
        return self.proxied_schema.load(*args, **kwargs)

    @override
    def dump(self, *args: Any, **kwargs: Any) -> Any:
        """Dump data using the lazily-resolved proxied schema."""
        return self.proxied_schema.dump(*args, **kwargs)
