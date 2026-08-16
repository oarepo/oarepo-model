#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Data type for internal (same-record) relations.

This module provides the InternalRelationDataType data type for creating
relationships that resolve against a part of the *same* record instead of an
externally PID-resolved one, built on top of
`oarepo_runtime.records.systemfields.relations.InternalRelation` (see
https://github.com/oarepo/oarepo-runtime/pull/420).

An internal relation's target is always the model currently being built - it
can never be introspected eagerly the way PIDRelation.create_mapping/
create_json_schema/etc. can for an already-built external model, since the
model that owns the target_paths is still under construction while this data
type's create_* methods run. Every InternalRelationDataType field is therefore
always resolved lazily, reusing (and, where the shape differs because there
may be several target_paths instead of a single target model, extending) the
Lazy* helpers PIDRelation already uses for its own self-referencing case - see
relations.py.

The `internal_relations = InternalRelations()` lookup-table system field itself
(needed on the Record class for this data type's fields to actually resolve at
runtime) is wired up by `presets.internal_relations.internal_relations_preset`
- see that package's `InternalRelationsLookupPreset`. See ir.md (repository
root) for the remaining design discussion and TODO list (most notably: the
same wiring for the Draft class).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar, cast, override

import marshmallow
from invenio_records.systemfields.relations import RelationsField
from oarepo_runtime.proxies import current_runtime

from oarepo_model.customizations.high_level.add_internal_relation import AddInternalRelation
from oarepo_model.customizations.high_level.add_pid_relation import AddLazyRelation, RelationFieldCustomization

from .base import DataType
from .collections import ObjectDataType
from .relations import (
    LazyModelJSONFile,
    LazyProxiedMarshmallowSchema,
    LazyUIModelChildren,
    key_names_from_keys,
    relation_name_from_path,
    relation_path_from_customization_path,
    resolve_declared_root_properties,
    set_key_model,
)

if TYPE_CHECKING:
    from types import SimpleNamespace

    from invenio_records.systemfields.relations import RelationBase

    from oarepo_model.customizations.base import Customization

log = logging.getLogger("oarepo_model")


def _walk_type_tree_path(root: dict[str, Any] | None, path: str) -> dict[str, Any] | None:
    """Walk a dotted path down a "type"/"properties"/"items"-shaped tree.

    This shape is shared by the raw declarative type dicts (model_metadata.types,
    see resolve_declared_root_properties) and the generated JSON schema
    (create_json_schema's output) - an object node nests via "properties", an
    array node nests via "items" first. Returns the "properties" mapping of the
    node found at `path`, or None if any segment is missing or not an object
    (e.g. a target_path that does not (yet) exist in the schema).
    """
    props: Any = root
    for part in path.split("."):
        if not isinstance(props, dict) or part not in props:
            return None
        node = props[part]
        if not isinstance(node, dict):
            return None
        if node.get("type") == "array":
            node = node.get("items")
            if not isinstance(node, dict):
                return None
        props = node.get("properties")
    return props if isinstance(props, dict) else None


def _walk_mapping_path(root: dict[str, Any] | None, path: str) -> dict[str, Any] | None:
    """Walk a dotted path down an OpenSearch mapping's "properties" tree.

    Unlike _walk_type_tree_path, OpenSearch mappings have no separate array
    type to unwrap - a repeated object field is mapped exactly like a single
    one (see LazyMapping in relations.py for the same convention).
    """
    props: Any = root
    for part in path.split("."):
        if not isinstance(props, dict) or part not in props:
            return None
        node = props[part]
        if not isinstance(node, dict):
            return None
        props = node.get("properties")
    return props if isinstance(props, dict) else None


def _walk_ui_model_path(root: dict[str, Any] | None, path: str) -> dict[str, Any] | None:
    """Walk a dotted path down a ui model's "children" tree.

    Mirrors _walk_mapping_path/_walk_type_tree_path, but ui model nodes nest
    via "children" for object-shaped fields and via "child" (wrapping another
    node with its own "children") for array-shaped ones - see
    ArrayDataType.create_ui_model/ObjectDataType.create_ui_model.
    """
    children: Any = root
    for part in path.split("."):
        if not isinstance(children, dict) or part not in children:
            return None
        node = children[part]
        if not isinstance(node, dict):
            return None
        if "child" in node:
            node = node["child"]
            if not isinstance(node, dict):
                return None
        children = node.get("children")
    return children if isinstance(children, dict) else None


def _unwrap_nested_field(field: marshmallow.fields.Field | None) -> marshmallow.fields.Nested | None:
    """Return the Nested field to descend into for a (possibly array-wrapped) marshmallow field.

    ArrayDataType.create_marshmallow_field produces a plain fields.List wrapping
    the item field (see ArrayDataType._get_marshmallow_field_args) rather than a
    Nested field itself - a target_path segment pointing at an array field (e.g.
    "metadata.proteins") must unwrap one level of List first. Returns None if
    `field` is neither, or the unwrapped inner field is not Nested either.
    """
    if isinstance(field, marshmallow.fields.List):
        field = field.inner
    return field if isinstance(field, marshmallow.fields.Nested) else None


def _merge_across_target_paths(
    resolve_one: Any,
    target_paths: list[str],
) -> dict[str, Any]:
    """Merge the per-target_path property mappings `resolve_one` returns into one.

    Earlier target_paths win on key collisions, mirroring
    InternalRelationResult.resolve()'s runtime behaviour of trying each
    target_path in order and returning the first match.
    """
    merged: dict[str, Any] = {}
    for target_path in target_paths:
        for key, value in (resolve_one(target_path) or {}).items():
            merged.setdefault(key, value)
    return merged


class LazyInternalMapping(LazyModelJSONFile):
    """Lazily resolves an internal-relation's mapping properties across its target_paths."""

    def __init__(self, model: str, target_paths: list[str], keys: list[str] | None = None) -> None:
        """Initialize with the (self-referencing) model name, target_paths and keys."""
        super().__init__(model, keys, "internal/primary_mapping.json")
        self._target_paths = target_paths

    @override
    def _get_source_properties(self, loaded: Any) -> dict[str, Any]:
        root = cast("dict[str, Any]", loaded["mappings"]["properties"])
        return _merge_across_target_paths(lambda p: _walk_mapping_path(root, p), self._target_paths)

    @override
    def _ensure(self) -> None:
        super()._ensure()
        # see the matching comment in relations.py's LazyMapping._ensure - the
        # "@v" marker is always present on a dereferenced relation object.
        if "@v" not in self._data:
            self._data["@v"] = {"type": "keyword", "ignore_above": 256}


class LazyInternalJSONSchema(LazyModelJSONFile):
    """Lazily resolves an internal-relation's json schema properties across its target_paths."""

    def __init__(self, model: str, target_paths: list[str], keys: list[str] | None = None) -> None:
        """Initialize with the (self-referencing) model name, target_paths and keys."""
        super().__init__(model, keys, "internal/primary_jsonschema.json")
        self._target_paths = target_paths

    @override
    def _get_source_properties(self, loaded: Any) -> dict[str, Any]:
        root = cast("dict[str, Any]", loaded["properties"])
        return _merge_across_target_paths(lambda p: _walk_type_tree_path(root, p), self._target_paths)

    @override
    def _ensure(self) -> None:
        super()._ensure()
        # see the matching comment in relations.py's LazyJSONSchema._ensure.
        if "@v" not in self._data:
            self._data["@v"] = {"type": "string"}


class LazyInternalUIModelChildren(LazyUIModelChildren):
    """Lazily resolves an internal-relation's UI model 'children' across its target_paths."""

    def __init__(self, model: str, target_paths: list[str], keys: list[str] | None = None) -> None:
        """Initialize with the (self-referencing) model name, target_paths and keys."""
        super().__init__(model, keys)
        self._target_paths = target_paths

    @override
    def _get_source_properties(self) -> dict[str, Any]:
        root = super()._get_source_properties()
        return _merge_across_target_paths(lambda p: _walk_ui_model_path(root, p), self._target_paths)


class LazyProxiedInternalMarshmallowSchema(LazyProxiedMarshmallowSchema):
    """Lazily builds a marshmallow schema by resolving 'keys' across multiple target_paths.

    Concrete subclasses (LazyInternalMarshmallowSchema/LazyInternalUIMarshmallowSchema)
    additionally set `target_paths` (on top of `model`/`keys`, see
    LazyProxiedMarshmallowSchema) - each `keys` entry is resolved against the
    first target_path whose (possibly nested) schema actually has it, mirroring
    InternalRelationResult.resolve()'s "try every target_path in order" runtime
    behaviour.
    """

    target_paths: ClassVar[list[str]] = []

    @classmethod
    def _descend(cls, schema: marshmallow.Schema, path: str) -> marshmallow.Schema | None:
        """Follow a dotted target_path down nested marshmallow schemas.

        Returns None if any segment along the way is missing or not a Nested
        field - the target_path may legitimately not (yet) exist on the
        schema, same as _walk_type_tree_path/_walk_mapping_path/_walk_ui_model_path.
        """
        for part in path.split("."):
            field = schema.fields.get(part)
            nested = _unwrap_nested_field(field)
            if nested is None:
                return None
            schema = nested.schema
        return schema

    @classmethod
    def _resolve_field(
        cls,
        target_schemas: list[marshmallow.Schema | None],
        parts: list[str],
    ) -> marshmallow.fields.Field | None:
        for target_schema in target_schemas:
            if target_schema is None:
                continue
            source_schema = target_schema
            try:
                for part in parts[:-1]:
                    nested = _unwrap_nested_field(source_schema.fields[part])
                    if nested is None:
                        raise TypeError(f"Field {part!r} is not a nested field.")
                    source_schema = nested.schema
                return source_schema.fields[parts[-1]]
            except (KeyError, TypeError):
                continue
        return None

    @classmethod
    @override
    def _create_proxied_marshmallow(cls) -> type[marshmallow.Schema]:
        own_schema = cls._get_target_schema()
        target_schemas = [cls._descend(own_schema, path) for path in cls.target_paths]

        tree: dict[str, Any] = {}
        for key in cls.keys or []:
            parts = key.split(".")
            dest = tree
            for part in parts[:-1]:
                dest = dest.setdefault(part, {})
            field = cls._resolve_field(target_schemas, parts)
            dest[parts[-1]] = field if field is not None else cls._missing_field(key)

        return cls._build_schema_class(cls.__name__, tree)


class LazyInternalMarshmallowSchema(LazyProxiedInternalMarshmallowSchema):
    """Lazily resolves an internal-relation's marshmallow schema across its target_paths."""

    @classmethod
    @override
    def _get_target_schema(cls) -> marshmallow.Schema:
        schema_cls = cast(
            "type[marshmallow.Schema]",
            current_runtime.models[cls.model].service_config.schema,
        )
        return schema_cls()


class LazyInternalUIMarshmallowSchema(LazyProxiedInternalMarshmallowSchema):
    """Lazily resolves an internal-relation's UI marshmallow schema across its target_paths."""

    @classmethod
    @override
    def _get_target_schema(cls) -> marshmallow.Schema:
        namespace = cast("SimpleNamespace", current_runtime.models[cls.model].namespace)
        return namespace.RecordUISchema()

    @classmethod
    @override
    def _missing_field(cls, key: str) -> marshmallow.fields.Field:
        # not every field has a UI-specific counterpart - see the matching
        # LazyUIMarshmallowSchema._missing_field in relations.py.
        return marshmallow.fields.Raw()


class InternalRelationDataType(ObjectDataType):
    """Relation to a part of the same record, resolved via an InternalRelations lookup table.

    Usage:
    ```yaml
    a:
        type: internal-relation
        target_paths:
        - metadata.proteins
        - metadata.instruments
        keys:
        - id
        - name

        # required - see _model()/ir.md for why this is needed and how it
        # could be made implicit; must equal the enclosing model's own name,
        # since an internal relation always resolves within the same record.
        model: "my_own_model"

        relation_field_kwargs: {}  # optional, forwarded to InternalRelation(**kwargs)
        properties: {...}          # optional escape hatch, see _get_properties
    ```

    Note: for this to actually resolve at runtime, the model must also include
    `presets.internal_relations.internal_relations_preset`, which adds the
    `internal_relations = InternalRelations()` lookup-table system field to
    the Record class (Draft support is still a TODO - see ir.md).
    """

    TYPE = "internal-relation"

    marshmallow_field_class = marshmallow.fields.Nested

    def _target_paths(self, element: dict[str, Any]) -> list[str]:
        """Return the (required) 'target_paths' declared on the element."""
        target_paths = element.get("target_paths")
        if not target_paths:
            raise ValueError(
                "'target_paths' key is required for an internal-relation element.",
            )
        return list(target_paths)

    def _model(self, element: dict[str, Any]) -> str:
        """Return the (required) 'model' declared on the element.

        Always a self-reference (an internal relation resolves within the
        record it is declared on), but is still required explicitly rather
        than inferred: create_mapping/create_json_schema/create_marshmallow_schema/
        etc. are called by several different presets, none of which currently
        pass the InvenioModel being built down to the data type - see ir.md
        for the ergonomics/architecture trade-off this involves.
        """
        model = element.get("model")
        if not model:
            raise ValueError(
                "'model' key is required for an internal-relation element - set it "
                "to the enclosing model's own name (an internal relation always "
                "resolves within the same record - see ir.md).",
            )
        return cast("str", model)

    @override
    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
        path_suffix: str = "",
    ) -> Any:
        """Create facets for the internal-relation's own 'keys'.

        Mirrors PIDRelation.get_facet's self-referencing branch - an internal
        relation's target_paths always point into the model currently being
        built, so (unlike create_mapping/create_json_schema/create_relations/
        create_ui_model) there is nowhere to defer facet generation to (facet
        *names* must be known synchronously, at build time - see
        RecordFacetsPreset/MetadataFacetsPreset). No facets are generated for
        this relation's keys unless 'properties' is declared explicitly.
        """
        _ = path_suffix

        if "properties" not in element:
            log.warning(
                "Cannot generate facets for the internal-relation's 'keys' because "
                "its target_paths %r point into the model currently being built and "
                "can not be introspected yet. No facets will be generated for this "
                "relation's keys - declare 'properties' explicitly if this is not "
                "sufficient.",
                element.get("target_paths"),
            )
            return facets

        for key, value in self._get_properties(element).items():
            if key == "@v":
                continue
            if path == "":
                _path = key
            elif path.endswith(key):
                _path = path
            else:
                _path = path + "." + key
            facets.update(self._registry.get_type(value).get_facet(_path, value, nested_facets, facets))

        return facets

    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        """Get the (explicit or keyword-fallback) properties for this relation's 'keys'.

        Unlike PIDRelation._get_properties, there is no eager branch - an
        internal relation's target_paths can never be introspected while the
        model that owns them is still being built (see the module docstring),
        so this always falls back to "keyword" per key, same as PIDRelation's
        own self-referencing fallback.
        """
        if "properties" in element:
            if not isinstance(element["properties"], dict):
                raise TypeError(
                    f"Expected 'properties' to be a dict, got {type(element['properties'])}.",
                )
            return cast("dict[str, Any]", element["properties"])

        log.warning(
            "Cannot determine the properties of the internal-relation's 'keys' "
            "because its target_paths %r point into the model currently being "
            "built. Falling back to 'keyword' for every key - declare 'properties' "
            "explicitly if this is not sufficient.",
            element.get("target_paths"),
        )

        ret: dict[str, Any] = {}
        for key in element.get("keys", []):
            if isinstance(key, str):
                set_key_model(ret, key, {"type": "keyword"})
            elif isinstance(key, dict):
                for k, v in key.items():
                    set_key_model(ret, k, v)
            else:
                raise TypeError(f"Invalid key type: {type(key)}")
        if "id" not in ret:
            ret["id"] = {"type": "keyword"}
        if "@v" not in ret:
            ret["@v"] = {"type": "keyword", "skip_marshmallow": True}
        return ret

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        return {
            **DataType.create_mapping(self, element),
            "dynamic": "strict",
            "properties": LazyInternalMapping(
                self._model(element),
                self._target_paths(element),
                element.get("keys", []),
            ),
        }

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        return {
            **DataType.create_json_schema(self, element),
            "unevaluatedProperties": False,
            "properties": LazyInternalJSONSchema(
                self._model(element),
                self._target_paths(element),
                element.get("keys", []),
            ),
        }

    @override
    def create_marshmallow_schema(self, element: dict[str, Any]) -> type[marshmallow.Schema]:
        return type(
            self.name,
            (LazyInternalMarshmallowSchema,),
            {
                "model": self._model(element),
                "target_paths": self._target_paths(element),
                "keys": element.get("keys", []),
            },
        )

    @override
    def create_ui_marshmallow_schema(self, element: dict[str, Any]) -> type[marshmallow.Schema]:
        return type(
            self.name,
            (LazyInternalUIMarshmallowSchema,),
            {
                "model": self._model(element),
                "target_paths": self._target_paths(element),
                "keys": element.get("keys", []),
            },
        )

    @override
    def create_ui_model(
        self,
        element: dict[str, Any],
        path: list[str],
    ) -> dict[str, Any]:
        ret = DataType.create_ui_model(self, element, path)
        ret["children"] = LazyInternalUIModelChildren(
            self._model(element),
            self._target_paths(element),
            element.get("keys", []),
        )
        return ret

    @override
    def create_relations(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> list[Customization]:
        relation_path = relation_path_from_customization_path(path)
        relation_name = relation_name_from_path(relation_path)
        target_paths = self._target_paths(element)
        key_names = key_names_from_keys(element.get("keys", []))

        relations: list[Customization] = [
            AddInternalRelation(
                name=relation_name,
                path=relation_path,
                keys=key_names,
                target_paths=target_paths,
                **element.get("relation_field_kwargs", {}),
            ),
        ]

        if "properties" not in element:
            relations.append(AddLazyRelation(lambda: self._resolve_nested_relation_fields(element, path)))
        else:
            relations.extend(self._discover_nested_relation_customizations(element, path))

        return relations

    def _discover_nested_relation_customizations(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> list[Customization]:
        """Walk this relation's nested (explicitly declared) properties for further relations."""
        result: list[Customization] = []
        for prop_name, prop in self._get_properties(element).items():
            result.extend(
                self._registry.get_type(prop).create_relations(
                    prop,
                    [*path, (prop_name, prop)],
                ),
            )
        return result

    def _resolve_nested_relation_fields(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> dict[str, RelationBase]:
        """Materialize this relation's nested relation fields, called lazily.

        Mirrors PIDRelation._resolve_nested_relation_fields, but the tree to
        walk is the union of the (by then fully built and registered) own
        model's declared schema at each of this relation's target_paths,
        instead of a single external target's schema.
        """
        own_model = self._model(element)
        root_properties = resolve_declared_root_properties(f"runtime_models_{own_model}")
        merged_properties = _merge_across_target_paths(
            lambda p: _walk_type_tree_path(root_properties, p),
            self._target_paths(element),
        )

        fields: dict[str, RelationBase] = {}
        for prop_name, prop in merged_properties.items():
            for customization in self._registry.get_type(prop).create_relations(prop, [*path, (prop_name, prop)]):
                if not isinstance(customization, RelationFieldCustomization):
                    continue
                for name, field in customization.build_relation_fields().items():
                    if isinstance(field, RelationsField):
                        # see the matching comment in PIDRelation._resolve_nested_relation_fields.
                        fields.update(field._fields)
                    else:
                        fields[name] = field
        return fields
