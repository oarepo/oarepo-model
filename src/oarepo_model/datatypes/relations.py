#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Data type for PID-based record relations.

This module provides the PIDRelation data type for creating relationships
between records using persistent identifiers (PIDs). It extends the ObjectDataType
to handle record references with configurable keys, PID fields, and caching
mechanisms. The data type automatically generates the necessary relation
customizations for the model builder.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping
from functools import cached_property
from importlib import import_module
from typing import TYPE_CHECKING, Any, cast, override

import marshmallow
from flask import json
from invenio_base.utils import obj_or_import_string
from oarepo_model.utils import JSONContent
from oarepo_runtime.proxies import current_runtime

from oarepo_model.customizations.high_level.add_pid_relation import (
    ARRAY_PATH_ITEM,
    AddPIDRelation,
)
from oarepo_model.register import FileContent

from .base import DataType
from .collections import ObjectDataType

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from invenio_records_resources.records.systemfields.pid import (
        PIDFieldContext,
    )

    from oarepo_model.customizations.base import Customization


class LazyModelPIDField:
    """Lazily resolves a model PID field by name."""

    def __init__(self, model_name: str) -> None:
        """Initialize with the model name to resolve."""
        self.model_name = model_name

    @cached_property
    def _real_field(self) -> PIDFieldContext:
        """Return the model PID field."""
        return current_runtime.models[self.model_name].record_cls.pid

    def resolve(self, *args: Any, **kwargs: Any) -> Any:
        """Resolve the model PID field by name."""
        return self._real_field.resolve(*args, **kwargs)


class LazyRecordPIDField:
    """Lazily resolves a record PID field by name."""

    def __init__(self, record_qname: str) -> None:
        """Initialize with the record qualified name to resolve."""
        self.record_qname = record_qname

    @cached_property
    def _real_field(self) -> PIDFieldContext:
        """Return the record PID field."""
        rec = obj_or_import_string(self.record_qname)
        if rec is None:
            raise ValueError(f"Record class {self.record_qname} could not be imported.")
        return rec.pid

    def resolve(self, *args: Any, **kwargs: Any) -> Any:
        """Resolve the model PID field by name."""
        return self._real_field.resolve(*args, **kwargs)


class LazyModelJSONFile(Mapping):
    """Lazily loads and exposes a JSON file from another model's namespace.

    Resolution is deferred to first use, since the target model (e.g. a
    self-referencing relation's own model) may not be registered/importable
    yet while this object is created.
    """

    def __init__(self, model: str, keys: list[str] | None, filename: str) -> None:
        """Initialize with the model name, keys and namespace file name to resolve."""
        self._model = model
        self._keys = keys
        self._filename = filename
        self._data: dict[str, Any] = {}

    def _load_json(self) -> Any:
        """Load and parse the JSON file content from the target model's namespace."""
        ns_files = current_runtime.models[self._model].namespace.__files__
        file_content = ns_files[self._filename]
        if isinstance(file_content, JSONContent):
            return file_content.payload
        return json.loads(file_content)

    @abstractmethod
    def _get_source_properties(self, loaded: Any) -> dict[str, Any]:
        """Return the "properties" mapping of the loaded JSON content to look keys up in."""
        raise NotImplementedError

    def _ensure(self) -> None:
        """Resolve the data on first use."""
        if self._data:
            return
        loaded = self._load_json()

        self._data = generated = {}

        source_properties = self._get_source_properties(loaded)

        for key in self._keys or []:
            if "." not in key:
                # no nesting - just copy the field's definition as-is
                generated[key] = source_properties[key]
                continue

            # nested key - walk down both the source (loaded) and the
            # destination (generated) in lockstep, creating the intermediate
            # "type": "object" / "properties" levels in the destination as we go.
            parts = key.split(".")
            source = source_properties
            dest = generated
            for part in parts[:-1]:
                source = source[part]["properties"]
                dest = dest.setdefault(part, {"type": "object", "properties": {}})["properties"]
            dest[parts[-1]] = source[parts[-1]]

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


class LazyMapping(LazyModelJSONFile):
    """Lazily resolves a relation's mapping properties from the target model's mapping."""

    def __init__(self, model: str, keys: list[str] | None = None) -> None:
        """Initialize with the model name and keys to resolve."""
        super().__init__(model, keys, "internal/primary_mapping.json")

    @override
    def _get_source_properties(self, loaded: Any) -> dict[str, Any]:
        return loaded["mappings"]["properties"]

    @override
    def _ensure(self) -> None:
        """Resolve the mapping data on first use."""
        super()._ensure()

        # invenio_records always stamps a "@v" (revision) marker onto every
        # dereferenced relation object (see RelationResult._dereference_one in
        # invenio_records), regardless of what is listed in "keys" - it must be
        # declared here too, or a strict mapping rejects it at index time.
        if "@v" not in self._data:
            self._data["@v"] = {"type": "keyword", "ignore_above": 256}


class LazyJSONSchema(LazyModelJSONFile):
    """Lazily resolves a relation's json schema properties from the target model's json schema."""

    def __init__(self, model: str, keys: list[str] | None = None) -> None:
        """Initialize with the model name and keys to resolve."""
        super().__init__(model, keys, "internal/primary_jsonschema.json")

    @override
    def _get_source_properties(self, loaded: Any) -> dict[str, Any]:
        return loaded["properties"]

    @override
    def _ensure(self) -> None:
        """Resolve the json schema data on first use."""
        super()._ensure()

        # see the matching comment in LazyMapping._ensure - the "@v" marker is
        # always present on a dereferenced relation object.
        if "@v" not in self._data:
            self._data["@v"] = {"type": "string"}


class PIDRelation(ObjectDataType):
    """Relation to another record using a PID.

    Usage:
    ```yaml
    a:
        type: pid-relation
        keys:
        - id
        - metadata.title:
            type: i18nstr

        # one of the following items is required
        model: "my_other_model"
        record_cls: "my_other_model.records:record" or class
        pid_field: "my_module:pid_field_getter" or PIDField instance

        cache_key: "my_cache_key" (optional, used for caching the resolved record)
    ```
    """

    TYPE = "pid-relation"

    marshmallow_field_class = marshmallow.fields.Nested

    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
        path_suffix: str = "",
    ) -> Any:
        """Create facets for the data type."""
        _, _, _, _, _ = path, element, nested_facets, facets, path_suffix

        return facets

    def _needs_lazy_access(self, element: dict[str, Any]) -> bool:
        """Check whether this pid-relation's target can be resolved right now.

        Returns True if the model/record class this relation points to can not be
        imported yet (e.g. a relation referencing the model that is currently being
        built), meaning any access into the target's schema must be deferred.
        """
        target = element.get("record_cls") or element.get("model")
        if not isinstance(target, str):
            return False
        try:
            obj_or_import_string(target)
        except ImportError:
            return True
        return False

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create a mapping for the data type.

        Resolving the properties eagerly (as ObjectDataType.create_mapping does)
        requires the referenced model's schema/record class. If that is not
        available yet (self-referencing relations), the "properties" key is
        backed by a LazyMapping that is only resolved on first use instead.
        """
        if not self._needs_lazy_access(element):
            return super().create_mapping(element)

        if 'model' not in element:
            raise ValueError("'model' key is required for lazy mapping")

        model = element['model']
        keys = element.get('keys', [])

        return {
            **DataType.create_mapping(self, element),
            "dynamic": "strict",
            "properties": LazyMapping(model, keys),
        }

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create a json schema for the data type.

        Resolving the properties eagerly (as ObjectDataType.create_json_schema
        does) requires the referenced model's schema/record class. If that is not
        available yet (self-referencing relations), the "properties" key is
        backed by a LazyJSONSchema that is only resolved on first use instead.
        """
        if not self._needs_lazy_access(element):
            return super().create_json_schema(element)

        if "model" not in element:
            raise ValueError("'model' key is required for lazy json schema")

        model = element["model"]
        keys = element.get("keys", [])

        return {
            **DataType.create_json_schema(self, element),
            "unevaluatedProperties": False,
            "properties": LazyJSONSchema(model, keys),
        }

    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        if "properties" in element:
            if not isinstance(element["properties"], dict):
                raise TypeError(
                    f"Expected 'properties' to be a dict, got {type(element['properties'])}.",
                )
            return cast("dict[str, Any]", element["properties"])
        ret: dict[str, Any] = {}
        for key in element["keys"]:
            if isinstance(key, str):
                set_key_model(ret, key, {"type": "keyword"})
            elif isinstance(key, dict):
                for k, v in key.items():
                    set_key_model(ret, k, v)
            else:
                raise TypeError(f"Invalid key type: {type(key)}")
        # if 'id' is not in keys, add it as a keyword field
        if "id" not in ret:
            ret["id"] = {"type": "keyword"}
        # if @v is not in keys, add it as a keyword field, set marshmallow as dump only
        if "@v" not in ret:
            ret["@v"] = {"type": "keyword", "skip_marshmallow": True}
        return ret

    @override
    def create_relations(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> list[Customization]:
        relation_path = self._relation_path(element, path)
        relation_name = self._relation_name(element, path)
        pid_field = self._pid_field(element, path)
        cache_key = self._cache_key(element, path)
        key_names = self._key_names(element, path)

        relations: list[Customization] = [
            AddPIDRelation(
                name=relation_name,
                path=relation_path,
                keys=key_names,
                pid_field=pid_field,
                cache_key=cache_key,
                **element.get("relation_field_kwargs", {}),
            ),
        ]

        for prop_name, prop in self._get_properties(element).items():
            relations.extend(
                self._registry.get_type(prop).create_relations(
                    prop,
                    [*path, (prop_name, prop)],
                ),
            )

        return relations

    def _relation_path(
        self,
        element: dict[str, Any],  # noqa: ARG002
        path: list[tuple[str, dict[str, Any]]],
    ) -> list:
        """Get the relation path for the PID relation."""
        relation_path: list[str | type[ARRAY_PATH_ITEM]] = []
        for pth in path:
            if pth[0] == "":
                relation_path.append(ARRAY_PATH_ITEM)
            else:
                relation_path.append(pth[0])
        return relation_path

    def _relation_name(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> str:
        relation_path = self._relation_path(element, path)
        return ".".join(str(k) for k in relation_path if k is not ARRAY_PATH_ITEM)

    def _pid_field(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],  # noqa: ARG002
    ) -> PIDFieldContext | LazyRecordPIDField | LazyModelPIDField:
        """Get the PID field from the element."""
        if "pid_field" in element:
            pidf = cast(
                "Callable[[dict[str, Any]], PIDFieldContext]",
                obj_or_import_string(element["pid_field"]),
            )
            if pidf is None or not callable(pidf):
                raise ValueError(
                    f"PID field {element['pid_field']} could not be imported.",
                )
            return pidf(element)
        if "record_cls" in element:
            try:
                rec = obj_or_import_string(element["record_cls"])
            except ImportError:
                return LazyRecordPIDField(element["record_cls"])
            if rec is None or not hasattr(rec, "pid"):
                raise ValueError(
                    f"Record class {element['record_cls']} does not have a 'pid' attribute.",
                )
            return rec.pid
        if "model" in element:
            try:
                imported_model = obj_or_import_string(element["model"])
            except ImportError:
                return LazyModelPIDField(element["model"])

            if imported_model is None:
                raise ValueError(
                    f"Model {element['model']} could not be imported.",
                )
            rec = getattr(imported_model, "Record", None)
            if rec is None or not hasattr(rec, "pid"):
                raise ValueError(
                    f"Record class {rec} on model {element['model']} does not have a 'pid' attribute.",
                )
            return rec.pid

        raise ValueError(
            "Either 'pid_field' or 'record_cls' must be provided in the pid-relation element.",
        )

    def _cache_key(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],  # noqa: ARG002
    ) -> str | None:
        return element.get("cache_key")

    def _key_names(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],  # noqa: ARG002
    ) -> list[str]:
        keys = set()
        for key in element.get("keys", []):
            if isinstance(key, str):
                keys.add(key)
            elif isinstance(key, dict):
                keys.update(key.keys())
            else:
                raise TypeError(f"Invalid key type: {type(key)}")
        return list(keys)


def set_key_model(properties: dict[str, Any], key: str, value: Any) -> None:
    """Set a key-value pair in the properties dictionary."""
    parts = key.split(".")
    current = properties
    for part in parts[:-1]:
        if part not in current:
            current[part] = {
                "type": "object",
                "properties": {},
            }
        current = current[part]["properties"]
    current[parts[-1]] = value
