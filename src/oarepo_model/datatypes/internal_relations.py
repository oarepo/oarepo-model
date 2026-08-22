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

An internal relation is, structurally, a self-referencing relation (like
LazyPIDRelation's "lazy-pid-relation") whose target is a *sub-path* of the
current model instead of the model's root - its target can never be
introspected eagerly, since the model that owns `target_path` is still under
construction while this data type's create_* methods run. InternalRelationDataType
therefore extends LazyPIDRelation and reuses almost all of its lazy-resolution
machinery unchanged, only overriding the "where do I look" methods
(`_get_relation_model`, `_get_target_properties`) and the methods that must
build a different kind of relation field (`create_relations`) or thread an
extra `target_path` through (`create_mapping`/`create_json_schema`/
`create_ui_model`/`create_marshmallow_schema`/`create_ui_marshmallow_schema`).

The `internal_relations = InternalRelations()` lookup-table system field itself
(needed on the Record and Draft classes for this data type's fields to
actually resolve at runtime) is wired up by
`presets.internal_relations.internal_relations_preset` - see that package's
`InternalRelationsLookupPreset`/`InternalRelationsDraftLookupPreset`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, cast, override

import marshmallow

from oarepo_model.api import current_model
from oarepo_model.customizations.high_level.add_internal_relation import AddInternalRelation
from oarepo_model.customizations.high_level.add_pid_relation import AddLazyRelation
from oarepo_model.utils import import_runtime_model

from .collections import ObjectDataType
from .lazy_relations import (
    LazyPIDRelation,
    ReferenceJSONSchemaProperties,
    ReferenceMappingProperties,
    ReferenceMarshmallowSchema,
    ReferenceUIMarshmallowSchema,
    ReferenceUIModel,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from oarepo_model.customizations.base import Customization


def _walk_type_tree_path(root: dict[str, Any] | None, path: str) -> dict[str, Any] | None:
    """Walk a dotted path down a "type"/"properties"/"items"-shaped tree.

    This is the raw declarative type-tree shape (model_metadata.types, see
    InternalRelationDataType._get_target_properties) - an object node nests
    via "properties", an array node nests via "items" first. Returns the
    "properties" mapping of the node found at `path`, or None if any segment
    is missing or not an object (e.g. a target_path that does not exist).
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


def _descend_marshmallow_schema(schema: marshmallow.Schema, path: str) -> marshmallow.Schema | None:
    """Follow a dotted target_path down nested (possibly array-wrapped) marshmallow schemas.

    Returns None if any segment along the way is missing or not resolvable -
    the target_path may legitimately not (yet) exist on the schema.
    """
    if not path:
        return schema
    for part in path.split("."):
        nested = _unwrap_nested_field(schema.fields.get(part))
        if nested is None:
            return None
        schema = nested.schema
    return schema


class InternalReferenceMappingProperties(ReferenceMappingProperties):
    """Lazily resolves an internal-relation's mapping properties from its target_path."""

    def __init__(
        self,
        model: str,
        target_path: str,
        keys: list[str] | None,
        initial_content: Mapping[str, Any] | None = None,
    ) -> None:
        """Initialize with the (self-referencing) model name, target_path and keys."""
        super().__init__(model, keys, filename="record-mapping-link", initial_content=initial_content)
        self._target_path = target_path

    @override
    def _get_path(self, data: Any, path: str) -> dict[str, Any]:
        """Get the value at the given path in the data.

        OpenSearch mappings have no separate array wrapper (arrays are
        transparent), so descending target_path is structurally identical to
        descending a 'keys' entry - just feed the combined path to the
        regular (per-key) walk.
        """
        return super()._get_path(data, f"{self._target_path}.{path}")


class InternalReferenceJSONSchemaProperties(ReferenceJSONSchemaProperties):
    """Lazily resolves an internal-relation's json schema properties from its target_path."""

    def __init__(
        self,
        model: str,
        target_path: str,
        keys: list[str] | None,
        initial_content: Mapping[str, Any] | None = None,
    ) -> None:
        """Initialize with the (self-referencing) model name, target_path and keys."""
        super().__init__(model, keys, filename="record-jsonschema-link", initial_content=initial_content)
        self._target_path = target_path

    @override
    def _get_path(self, data: Any, path: str) -> dict[str, Any]:
        """Get the value at the given path in the data.

        Unlike a mapping, a json schema's array fields wrap their item
        schema under "items" - unwrap that at every target_path segment
        before handing off to the regular (never-array) per-key walk.
        """
        node_properties = data["properties"]
        for part in self._target_path.split("."):
            node = node_properties[part]
            if node.get("type") == "array":
                node = node["items"]
            node_properties = node["properties"]
        return super()._get_path({"properties": node_properties}, path)


class InternalReferenceUIModelChildren(ReferenceUIModel):
    """Lazily resolves an internal-relation's UI model 'children' from its target_path."""

    def __init__(
        self,
        model: str,
        target_path: str,
        keys: list[str] | None,
        initial_content: Mapping[str, Any] | None = None,
    ) -> None:
        """Initialize with the (self-referencing) model name, target_path and keys."""
        super().__init__(model, keys, filename="record-ui-model-link", initial_content=initial_content)
        self._target_path = target_path

    @override
    def _get_path(self, data: Any, path: str) -> dict[str, Any]:
        """Get the value at the given path in the data.

        A ui model's array fields wrap their item node under "child" - unwrap
        that at every target_path segment before handing off to the regular
        (never-array) per-key walk.
        """
        children = data.get("children", {})
        for part in self._target_path.split("."):
            node = children.get(part, {})
            if "child" in node:
                node = node["child"]
            children = node.get("children", {})
        return super()._get_path({"children": children}, path)


class LazyInternalMarshmallowSchema(ReferenceMarshmallowSchema):
    """Lazily resolves an internal-relation's marshmallow schema from its target_path."""

    target_path: ClassVar[str] = ""

    @classmethod
    @override
    def _get_target_schema(cls) -> marshmallow.Schema:
        """Return the (self-referencing) model's own schema, already descended to target_path."""
        schema = super()._get_target_schema()
        return _descend_marshmallow_schema(schema, cls.target_path) or marshmallow.Schema()


class LazyInternalUIMarshmallowSchema(ReferenceUIMarshmallowSchema):
    """Lazily resolves an internal-relation's UI marshmallow schema from its target_path."""

    target_path: ClassVar[str] = ""

    @classmethod
    @override
    def _get_target_schema(cls) -> marshmallow.Schema:
        """Return the (self-referencing) model's own UI schema, already descended to target_path."""
        schema = super()._get_target_schema()
        return _descend_marshmallow_schema(schema, cls.target_path) or marshmallow.Schema()


class InternalRelationDataType(LazyPIDRelation):
    """Relation to a part of the same record, resolved via an InternalRelations lookup table.

    Usage:
    ```yaml
    a:
        type: internal-relation
        target: metadata.proteins
        keys:
        - id
        - name

        relation_field_kwargs: {}  # optional, forwarded to InternalRelation(**kwargs)
    ```

    Note: for this to actually resolve at runtime, the model must also include
    `presets.internal_relations.internal_relations_preset`, which adds the
    `internal_relations = InternalRelations()` lookup-table system field to
    the Record class (and, if the model uses drafts, the Draft class too).
    """

    TYPE = "internal-relation"

    def _target_path(self, element: dict[str, Any]) -> str:
        """Return the (required) 'target' path declared on the element."""
        target = element.get("target")
        if not target:
            raise ValueError(
                "'target' key is required for an internal-relation element.",
            )
        return cast("str", target)

    def _model(self) -> str:
        """Return the name of the model currently being built.

        Always a self-reference (an internal relation resolves within the
        record it is declared on) - read from api.current_model, the
        ContextVar `_internal_model` sets for the whole duration of the
        build, rather than requiring an explicit (and always redundant)
        'model' element key.
        """
        model = current_model.get(None)
        if model is None:
            raise RuntimeError(
                "InternalRelationDataType can only be used while a model is "
                "being built (api.current_model is not set).",
            )
        return cast("str", model.name)

    @override
    def _get_relation_model(self, element: dict[str, Any], must_exist: bool = False) -> str:
        """Return the model currently being built - an internal relation's 'model' is always itself.

        Memoized onto `element` the first time it's resolved. _get_properties/
        _get_target_properties are called both eagerly (synchronously, during
        this model's own build, e.g. from create_mapping) and lazily (via the
        inherited _resolve_nested_relation_fields/AddLazyRelation, on first
        real `record.relations` access at runtime) - but api.current_model
        (which self._model() reads) is only ever set for the duration of the
        build, long gone by the time the lazy call happens. create_relations
        below forces this to resolve (and cache the result on `element`, the
        same object the lazy resolver's closure captures) while the build is
        still in progress, so the later lazy call finds it already cached.
        """
        model = element.get("_internal_relation_model")
        if model is None:
            model = self._model()
            element["_internal_relation_model"] = model
        return cast("str", model)

    @override
    def _get_target_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        """Resolve the (currently-being-built) model's own declared properties at target_path.

        Mirrors PIDRelation._get_target_properties, but anchored on this same
        model (self._get_relation_model()) instead of an externally-named
        one, and further descended to this relation's target_path.
        """
        imported = import_runtime_model(self._get_relation_model(element, must_exist=True))
        model_metadata = getattr(imported, "oarepo_model_arguments", {}).get("model_metadata")
        if model_metadata is None:
            return {}

        root: dict[str, Any] = {}
        if model_metadata.record_type:
            root.update(model_metadata.types.get(model_metadata.record_type, {}).get("properties", {}))
        if model_metadata.metadata_type:
            root["metadata"] = model_metadata.types.get(model_metadata.metadata_type, {})

        return _walk_type_tree_path(root, self._target_path(element)) or {}

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create a mapping for the data type.

        Always lazy (see the module docstring) - the lazy object itself *is*
        the mapping for this element (see LazyPIDRelation.create_mapping for
        why it isn't nested under an outer dict's "properties" key).
        """
        return cast(
            "dict[str, Any]",
            InternalReferenceMappingProperties(
                self._get_relation_model(element, must_exist=True),
                self._target_path(element),
                element.get("keys", []),
                initial_content=ObjectDataType.create_mapping(self, element),
            ),
        )

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create a json schema for the data type. Always lazy - see create_mapping."""
        return cast(
            "dict[str, Any]",
            InternalReferenceJSONSchemaProperties(
                self._get_relation_model(element, must_exist=True),
                self._target_path(element),
                element.get("keys", []),
                initial_content={
                    **ObjectDataType.create_json_schema(self, element),
                    "unevaluatedProperties": False,
                },
            ),
        )

    @override
    def create_marshmallow_schema(self, element: dict[str, Any]) -> type[marshmallow.Schema]:
        """Create a marshmallow schema for the data type.

        Always lazy - returns a LazyInternalMarshmallowSchema subclass that
        only builds the real schema on first load()/dump(), once target_path
        can be resolved.
        """
        return type(
            self.name,
            (LazyInternalMarshmallowSchema,),
            {
                "model": self._get_relation_model(element, must_exist=True),
                "target_path": self._target_path(element),
                "keys": element.get("keys", []),
            },
        )

    @override
    def create_ui_marshmallow_schema(self, element: dict[str, Any]) -> type[marshmallow.Schema]:
        """Create a UI marshmallow schema for the data type. Always lazy - see create_marshmallow_schema."""
        return type(
            self.name,
            (LazyInternalUIMarshmallowSchema,),
            {
                "model": self._get_relation_model(element, must_exist=True),
                "target_path": self._target_path(element),
                "keys": element.get("keys", []),
            },
        )

    @override
    def create_ui_model(
        self,
        element: dict[str, Any],
        path: list[str],
    ) -> dict[str, Any]:
        """Create a UI model for the data type. Always lazy - see create_mapping."""
        return cast(
            "dict[str, Any]",
            InternalReferenceUIModelChildren(
                self._get_relation_model(element, must_exist=True),
                self._target_path(element),
                element.get("keys", []),
                initial_content=ObjectDataType.create_ui_model(self, element, path),
            ),
        )

    @override
    def create_relations(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> list[Customization]:
        """Build the customizations that register this relation and discover any nested ones.

        Always emits an AddInternalRelation for the field itself. Nested
        relations inside the resolved target's own 'keys' are discovered
        lazily, via the inherited _resolve_nested_relation_fields/
        AddLazyRelation - target_path (like a self-referencing pid-relation's
        target) can never be introspected synchronously here, since it's a
        path inside the model currently being built.
        """
        relation_path = self._relation_path(element, path)
        relation_name = self._relation_name(element, path)
        key_names = self._relation_key_names(element, path)

        # Force _get_relation_model to resolve (and cache onto `element`) now,
        # while api.current_model is still set - see its docstring.
        self._get_relation_model(element, must_exist=True)

        relations: list[Customization] = [
            AddInternalRelation(
                name=relation_name,
                path=relation_path,
                keys=key_names,
                target_path=self._target_path(element),
                **element.get("relation_field_kwargs", {}),
            ),
        ]
        relations.append(
            AddLazyRelation(lambda: self._resolve_nested_relation_fields(element, path)),
        )
        return relations
