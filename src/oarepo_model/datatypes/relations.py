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

import copy
import logging
from abc import abstractmethod
from collections.abc import Mapping
from functools import cached_property
from typing import TYPE_CHECKING, Any, cast, override

import marshmallow
from flask import json
from invenio_base.utils import obj_or_import_string
from oarepo_runtime.proxies import current_runtime

from oarepo_model.customizations.high_level.add_pid_relation import (
    ARRAY_PATH_ITEM,
    AddPIDRelation,
)
from oarepo_model.utils import JSONContent

from .base import DataType
from .collections import ObjectDataType

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from types import SimpleNamespace

    from invenio_records_resources.records.systemfields.pid import (
        PIDFieldContext,
    )

    from oarepo_model.customizations.base import Customization

log = logging.getLogger("oarepo_model")


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
        namespace = cast("SimpleNamespace", current_runtime.models[self._model].namespace)
        ns_files = namespace.__files__
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
        return cast("dict[str, Any]", loaded["mappings"]["properties"])

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
        return cast("dict[str, Any]", loaded["properties"])

    @override
    def _ensure(self) -> None:
        """Resolve the json schema data on first use."""
        super()._ensure()

        # see the matching comment in LazyMapping._ensure - the "@v" marker is
        # always present on a dereferenced relation object.
        if "@v" not in self._data:
            self._data["@v"] = {"type": "string"}


class LazyProxiedMarshmallowSchema(marshmallow.Schema):
    """A marshmallow schema that lazily builds and delegates to the real schema.

    Concrete subclasses are created dynamically (see
    PIDRelation.create_marshmallow_schema/create_ui_marshmallow_schema) with
    `model`/`keys` class attributes set, and must implement `_get_target_schema`
    to return the (instantiated) schema `keys` should be resolved against.
    Resolving `keys` into actual fields requires the referenced model's schema,
    which is not available while a self-referencing model is still being built,
    so the real schema is only built on first load()/dump() call.
    """

    model: str
    keys: list[str] | None = None

    _proxied_schema: marshmallow.Schema | None = None

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

    @classmethod
    def _create_proxied_marshmallow(cls) -> type[marshmallow.Schema]:
        """Build the real marshmallow schema class for `model`/`keys`.

        First builds a tree - key (without dot) -> the target model's real
        marshmallow field, or (for keys with more path segments left) a nested
        dict of the same shape - then turns that tree into actual marshmallow
        Schema classes.
        """
        target_schema = cls._get_target_schema()

        # Step 1: descend into the target schema for each key, same as LazyMapping/
        # LazyJSONSchema do for the mapping/json schema, building a tree of
        # Field instances (leaves) and plain dicts (intermediate path segments).
        tree: dict[str, Any] = {}
        for key in cls.keys or []:
            parts = key.split(".")
            dest = tree
            for part in parts[:-1]:
                dest = dest.setdefault(part, {})
            try:
                source_schema = target_schema
                for part in parts[:-1]:
                    field = source_schema.fields[part]
                    if not isinstance(field, marshmallow.fields.Nested):
                        raise TypeError(
                            f"Field {part!r} on the path to {key!r} is not a nested field.",
                        )
                    source_schema = field.schema
                dest[parts[-1]] = source_schema.fields[parts[-1]]
            except KeyError, TypeError:
                dest[parts[-1]] = cls._missing_field(key)

        return cls._build_schema_class(cls.__name__, tree)

    @classmethod
    def _build_schema_class(cls, name: str, node: dict[str, Any]) -> type[marshmallow.Schema]:
        """Turn a tree built by _create_proxied_marshmallow into a Schema class.

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

    def _get_proxied_schema(self) -> marshmallow.Schema:
        """Return the (cached) real schema instance, building it on first use."""
        if self._proxied_schema is None:
            self._proxied_schema = self._create_proxied_marshmallow()()
        return self._proxied_schema

    @override
    def load(self, *args: Any, **kwargs: Any) -> Any:
        """Load data using the lazily-resolved proxied schema."""
        return self._get_proxied_schema().load(*args, **kwargs)

    @override
    def dump(self, *args: Any, **kwargs: Any) -> Any:
        """Dump data using the lazily-resolved proxied schema."""
        return self._get_proxied_schema().dump(*args, **kwargs)


class LazyMarshmallowSchema(LazyProxiedMarshmallowSchema):
    """Lazily resolves a relation's marshmallow schema from the target model's record schema."""

    @classmethod
    @override
    def _get_target_schema(cls) -> marshmallow.Schema:
        schema_cls = cast(
            "type[marshmallow.Schema]",
            current_runtime.models[cls.model].service_config.schema,
        )
        return schema_cls()


class LazyUIMarshmallowSchema(LazyProxiedMarshmallowSchema):
    """Lazily resolves a relation's UI marshmallow schema from the target model's UI record schema.

    Unlike the regular marshmallow schema, the UI schema is not registered on
    current_runtime.models's service config - it is only available as the
    "RecordUISchema" class on the target model's own runtime namespace.
    """

    @classmethod
    @override
    def _get_target_schema(cls) -> marshmallow.Schema:
        namespace = cast("SimpleNamespace", current_runtime.models[cls.model].namespace)
        return namespace.RecordUISchema()

    @classmethod
    @override
    def _missing_field(cls, key: str) -> marshmallow.fields.Field:
        # Not every field has a UI-specific counterpart (e.g. top-level "id" is
        # not part of the UI schema at all) - fall back to passing the value
        # through unchanged rather than failing.
        return marshmallow.fields.Raw()


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

    def _target_reference(self, element: dict[str, Any]) -> str | None:
        """Return the import string identifying this relation's target.

        'record_cls' is already a direct "module:Attr" import path. 'model'
        is the model's *base name* (e.g. "recursive_relation_test") and is
        not directly importable as-is - it has to be turned into its
        in-memory package name first (see InvenioModel.in_memory_package_name),
        which is only importable once that model has been built and
        `.register()`-ed.
        """
        if "record_cls" in element:
            target = element["record_cls"]
        elif "model" in element:
            target = element["model"]
            if isinstance(target, str):
                target = f"runtime_models_{target}"
        else:
            return None
        return target if isinstance(target, str) else None

    def _needs_lazy_access(self, element: dict[str, Any]) -> bool:
        """Check whether this pid-relation's target can be resolved right now.

        Returns True if the model/record class this relation points to can not be
        imported yet (e.g. a relation referencing the model that is currently being
        built), meaning any access into the target's schema must be deferred.
        """
        target = self._target_reference(element)
        if target is None:
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

        if "model" not in element:
            raise ValueError("'model' key is required for lazy mapping")

        model = element["model"]
        keys = element.get("keys", [])

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

    @override
    def create_marshmallow_schema(self, element: dict[str, Any]) -> type[marshmallow.Schema]:
        """Create a marshmallow schema for the data type.

        Resolving the properties eagerly (as ObjectDataType.create_marshmallow_schema
        does) requires the referenced model's schema/record class. If that is not
        available yet (self-referencing relations), a LazyMarshmallowSchema subclass
        is returned instead, which only builds the real schema on first load()/dump().
        """
        if not self._needs_lazy_access(element):
            return super().create_marshmallow_schema(element)

        if "model" not in element:
            raise ValueError("'model' key is required for lazy marshmallow schema")

        model = element["model"]
        keys = element.get("keys", [])

        return type(self.name, (LazyMarshmallowSchema,), {"model": model, "keys": keys})

    @override
    def create_ui_marshmallow_schema(self, element: dict[str, Any]) -> type[marshmallow.Schema]:
        """Create a UI marshmallow schema for the data type.

        Resolving the properties eagerly (as ObjectDataType.create_ui_marshmallow_schema
        does) requires the referenced model's schema/record class. If that is not
        available yet (self-referencing relations), a LazyUIMarshmallowSchema
        subclass is returned instead, which only builds the real schema on first
        load()/dump().
        """
        if not self._needs_lazy_access(element):
            return super().create_ui_marshmallow_schema(element)

        if "model" not in element:
            raise ValueError("'model' key is required for lazy ui marshmallow schema")

        model = element["model"]
        keys = element.get("keys", [])

        return type(self.name, (LazyUIMarshmallowSchema,), {"model": model, "keys": keys})

    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        if "properties" in element:
            if not isinstance(element["properties"], dict):
                raise TypeError(
                    f"Expected 'properties' to be a dict, got {type(element['properties'])}.",
                )
            return cast("dict[str, Any]", element["properties"])

        if self._needs_lazy_access(element):
            target = element.get("record_cls") or element.get("model")
            # This happens for self-referencing relations (a relation whose
            # target is the model that is currently being built) - the
            # target's real schema can not be introspected yet at this point,
            # so we fall back to the old "keyword for everything" behavior
            # below instead of hard-failing the whole model build. Relations
            # nested inside such a field's 'keys' (e.g. a vocabulary relation
            # copied in from the target) will not be discovered/dereferenced -
            # declare 'properties' explicitly to work around this.
            log.warning(
                "Cannot determine the properties of the pid-relation's 'keys' because "
                "the target model %r is not built yet (likely a self-referencing "
                "relation). Falling back to 'keyword' for every key - declare "
                "'properties' explicitly if this is not sufficient.",
                target,
            )
            target_properties: dict[str, Any] = {}
        else:
            target_properties = self._get_target_properties(element)

        ret: dict[str, Any] = {}
        for key in element["keys"]:
            if isinstance(key, str):
                prop = _lookup_property(target_properties, key)
                set_key_model(
                    ret,
                    key,
                    copy.deepcopy(prop) if prop is not None else {"type": "keyword"},
                )
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

    def _get_target_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        """Look up the already-built target model's real declarative schema tree.

        Returns a "properties"-style mapping (field name -> its declarative
        element dict, the same shape as this project's own model type dicts),
        merged from the target's record- and metadata-level schemas, so dotted
        'keys' entries like "metadata.title" can be resolved against the
        target's *real* field types (e.g. "vocabulary", "multilingual")
        instead of a hardcoded "keyword" guess.

        Returns an empty dict if the target can't be introspected this way
        (e.g. it was declared only via 'pid_field', or isn't an oarepo_model
        -built model) - callers fall back to "keyword" per key in that case.
        """
        target = self._target_reference(element)
        if target is None:
            return {}

        # 'target' may be "module:attr" (record_cls) or just "module" (model) -
        # either way, the model's namespace module itself is what carries
        # 'oarepo_model_arguments', so only the module part is needed here.
        imported = obj_or_import_string(target.split(":", 1)[0])
        model_metadata = getattr(imported, "oarepo_model_arguments", {}).get("model_metadata")
        if model_metadata is None:
            return {}

        properties: dict[str, Any] = {}
        if model_metadata.record_type:
            record_root = model_metadata.types.get(model_metadata.record_type, {})
            properties.update(record_root.get("properties", {}))
        if model_metadata.metadata_type:
            properties["metadata"] = model_metadata.types.get(model_metadata.metadata_type, {})
        return properties

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


def _lookup_property(properties: dict[str, Any], key: str) -> dict[str, Any] | None:
    """Walk a dotted key path down a properties tree, mirroring set_key_model.

    Returns None if any segment of the path is missing, so callers can fall
    back to a default rather than failing outright (e.g. for system fields
    like "id" that are never part of the declared properties tree).
    """
    parts = key.split(".")
    node = properties
    for part in parts[:-1]:
        prop = node.get(part)
        if not isinstance(prop, dict):
            return None
        node = prop.get("properties", {})
        if not isinstance(node, dict):
            return None
    return node.get(parts[-1])
