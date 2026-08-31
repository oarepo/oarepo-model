#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Data type for PID-based recursive record relations.

This module provides the PIDRecursiveRelation data type for creating relationships
between records using persistent identifiers (PIDs). It extends the ObjectDataType
to handle record references with configurable keys, PID fields, and caching
mechanisms. The data type automatically generates the necessary relation
customizations for the model builder.

Note: this data type should be used only for recursive relations, that is:
    * relation to the same model
    * circular references (model A references model B refecences model A)
"""

from __future__ import annotations

import logging
from functools import cached_property
from typing import TYPE_CHECKING, Any, cast, override

import marshmallow
from invenio_base.utils import obj_or_import_string
from invenio_records.systemfields.relations import RelationBase, RelationsField
from invenio_records_resources.records.systemfields.pid import (
    PIDFieldContext,
)
from oarepo_runtime.proxies import current_runtime

from oarepo_model.customizations.high_level.add_pid_relation import (
    AddLazyRelation,
    AddPIDRelation,
    RelationFieldCustomization,
)
from oarepo_model.datatypes.relations import PIDRelation
from oarepo_model.lazy import LazyJSONNamespaceFilePart, LazyMarshmallowSchema
from oarepo_model.utils import import_runtime_model, walk_type_tree_path

if TYPE_CHECKING:
    from collections.abc import Mapping
    from types import SimpleNamespace

    from oarepo_model.customizations.base import Customization


log = logging.getLogger("oarepo_model")


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
            return None # TODO: if there's no nested at the end of path?
        schema = nested.schema
    return schema


class LazyModelPIDFieldContext(PIDFieldContext):
    """Lazily resolves a PID field context by model name."""

    def __init__(self, model_name: str) -> None:
        """Initialize with the model name to resolve."""
        self.model_name = model_name

    @cached_property
    def _real_field(self) -> PIDFieldContext:
        """Return the model PID field."""
        return import_runtime_model(self.model_name).Record.pid

    def resolve(self, *args: Any, **kwargs: Any) -> Any:
        """Resolve the model PID field by name."""
        return self._real_field.resolve(*args, **kwargs)


class ReferenceMappingProperties(LazyJSONNamespaceFilePart):
    """Lazily resolves a relation's mapping properties from the target model's mapping."""

    extra_fields: Mapping[str, Any] = {
        "id": {"type": "keyword", "ignore_above": 256},
        "@v": {"type": "keyword", "ignore_above": 256},
    }

    def __init__(
        self,
        model: str,
        keys: list[str] | None,
        filename: str,
        initial_content: Mapping[str, Any] | None = None,
        target_path: str | None = None,
    ) -> None:
        """Initialize with the model name, keys, filename, and optional target_path.

        If target_path is provided, it will be prepended to all key paths when
        resolving from the source data.
        """
        super().__init__(model, keys, filename, initial_content)
        self._target_path = target_path

    @override
    def _get_path(self, data: Any, path: str) -> dict[str, Any]:
        """Get the value at the given path in the data."""
        if self._target_path:
            path = f"{self._target_path}.{path}"
        data = data["mappings"]
        for p in path.split("."):
            data = data["properties"]
            data = data[p]
        return cast("dict[str, Any]", data)

    @override
    def _set_path(self, data: Any, path: str, value: Any) -> None:
        """Set the value at the given path in the data.

        Note: in mapping, the value is always a dict, so we use `update` to merge it.
        """
        for p in path.split("."):
            data.setdefault("type", "object")
            data = data.setdefault("properties", {})
            data = data.setdefault(p, {})
        data.update(value)


class ReferenceJSONSchemaProperties(ReferenceMappingProperties):
    """Lazily resolves a relation's json schema properties from the target model's json schema."""

    extra_fields: Mapping[str, Any] = {
        "id": {"type": "string"},
        "@v": {"type": "string"},
    }

    @override
    def _get_path(self, data: Any, path: str) -> dict[str, Any]:
        """Get the value at the given path in the data."""
        # For JSON schema with target_path, concatenate paths and use walk_type_tree_path
        # which handles array unwrapping correctly
        combined_path = f"{self._target_path}.{path}" if self._target_path else path

        # Determine the root - mappings have "mappings" wrapper, JSON schema doesn't
        root = data.get("mappings", {}).get("properties") if "mappings" in data else data.get("properties") # TODO: why mappings here?

        # Use walk_type_tree_path to descend, but we need the leaf node, not its properties
        # So we descend to the parent, then get the leaf directly

        # TODO: this is duplication of walk_type_tree_path_leaf with raise KeyError on None
        # also - the mapping get_path is just a special case?
        parts = combined_path.split(".")
        if len(parts) == 1:
            # Single segment - just get from root
            result = root.get(parts[0]) if root else None
        else:
            # Multiple segments - use walk_type_tree_path for parent, then get leaf
            parent_path = ".".join(parts[:-1])
            leaf = parts[-1]
            parent_properties = walk_type_tree_path(root, parent_path)
            if parent_properties is None:
                raise KeyError(f"Path {parent_path!r} not found in JSON schema properties")
            result = parent_properties.get(leaf)

        if result is None:
            raise KeyError(f"Path {combined_path!r} not found in JSON schema properties")
        return cast("dict[str, Any]", result)

    # _set_path is inherited unchanged from ReferenceMappingProperties - a
    # json schema's "type: object" + "properties" + setdefault convention for
    # building a fresh output subtree is identical to a mapping's.


class ReferenceUIModel(LazyJSONNamespaceFilePart):
    """Lazily resolves a relation's UI model 'children' from the target model's own UI model."""

    extra_fields: Mapping[str, Any] = {
        "id": {
            "help": {"und": ""},
            "label": {"und": "id"},
            "hint": {"und": ""},
            "input": "keyword",
        },
        "@v": {
            "help": {"und": ""},
            "label": {"und": "@v"},
            "hint": {"und": ""},
            "input": "keyword",
        },
    }

    def __init__(
        self,
        model: str,
        keys: list[str] | None,
        filename: str,
        initial_content: Mapping[str, Any] | None = None,
        target_path: str | None = None,
    ) -> None:
        """Initialize with the model name, keys, filename, and optional target_path.

        If target_path is provided, it will be prepended to all key paths when
        resolving from the source data.
        """
        super().__init__(model, keys, filename, initial_content)
        self._target_path = target_path

    def _fallback_ui_model(self, key: str) -> dict[str, Any]:
        """Return a minimal UI model for a key that has no counterpart on the target's ui model."""
        return {
            "help": {"und": ""},
            "label": {"und": key},
            "hint": {"und": ""},
            "input": "keyword",
        }

    @override
    def _load_original_json(self) -> dict[str, Any]:
        """Load the original JSON content from the namespace file."""
        return cast("dict[str, Any]", import_runtime_model(self._model).ui_model)

    @override
    def _get_path(self, data: Any, path: str) -> dict[str, Any]:
        """Get the value at the given path in the data."""
        # For UI model, we need special handling: unwrap "child" at each target_path segment
        from oarepo_model.utils import walk_ui_model_path

        if self._target_path:
            # First descend to target_path (handling array unwrapping)
            children = walk_ui_model_path(data.get("children"), self._target_path)
            if children is None:
                raise KeyError(f"target_path {self._target_path!r} not found in UI model children")
            # Then descend further by the key path - walk_ui_model_path already gives us the children dict
            for p in path.split("."):
                children = children.get(p, {})
            return cast("dict[str, Any]", children)
        # No target_path - descend by the key path (same as original ReferenceUIModel._get_path)
        for p in path.split("."):
            data = data.get("children", {})
            data = data.get(p, {})
        return cast("dict[str, Any]", data)

    @override
    def _set_path(self, data: Any, path: str, value: Any) -> None:
        """Set the value at the given path in the data.

        Note: in json schemas, the value is always a dict, so we use `update` to merge it.
        """
        parts = path.split(".")
        for i, p in enumerate(parts):
            data = data.setdefault("children", {})
            if p not in data:
                data[p] = self._fallback_ui_model(p)
            data = data[p]
            if i < len(parts) - 1:
                # an intermediate path segment always represents a nested
                # object (it is about to get its own "children" on the next
                # iteration) - the leaf itself gets its real "input" (or the
                # "keyword" fallback) from `value`/the fallback below.
                data["input"] = "object"
        data.update(value)


class ReferenceMarshmallowSchema(LazyMarshmallowSchema):
    """Lazily resolves a relation's marshmallow schema from the target model's record schema.

    If the class has a `target_path` attribute, it will descend into that path
    before resolving keys (useful for internal relations).
    """

    @classmethod
    @override
    def _get_target_schema(cls) -> marshmallow.Schema:
        schema_cls = cast(
            "type[marshmallow.Schema]",
            current_runtime.models[cls.model].service_config.schema,
        )
        schema = schema_cls()
        # If target_path is set (e.g., for internal relations), descend into it
        target_path = getattr(cls, "target_path", None)
        if target_path:
            schema = _descend_marshmallow_schema(schema, target_path) or schema
        return schema


class ReferenceUIMarshmallowSchema(LazyMarshmallowSchema):
    """Lazily resolves a relation's UI marshmallow schema from the target model's UI record schema.

    Unlike the regular marshmallow schema, the UI schema is not registered on
    current_runtime.models's service config - it is only available as the
    "RecordUISchema" class on the target model's own runtime namespace.

    If the class has a `target_path` attribute, it will descend into that path
    before resolving keys (useful for internal relations).
    """

    @classmethod
    @override
    def _get_target_schema(cls) -> marshmallow.Schema:
        namespace = cast("SimpleNamespace", current_runtime.models[cls.model].namespace)
        schema = namespace.RecordUISchema()
        # If target_path is set (e.g., for internal relations), descend into it
        target_path = getattr(cls, "target_path", None)
        if target_path:
            schema = _descend_marshmallow_schema(schema, target_path) or schema
        return schema

    @classmethod
    @override
    def _missing_field(cls, key: str) -> marshmallow.fields.Field:
        # Not every field has a UI-specific counterpart (e.g. top-level "id" is
        # not part of the UI schema at all) - fall back to passing the value
        # through unchanged rather than failing.
        return marshmallow.fields.Raw()


class LazyPIDRelation(PIDRelation):
    """Relation to another record using a PID.

    Usage:
    ```yaml
    a:
        type: recursive-pid-relation
        model: "target model"      # target model's name
        keys:
        - id                       # dotted path to the field.
                                   # Definition will be looked up in the target model's schema.
        - metadata.title:          # dotted path to the field. Definition provided explicitly
            type: i18nstr
        cache_key: "my_cache_key"  # optional, used for caching the resolved record
    ```
    """

    TYPE = "lazy-pid-relation"

    marshmallow_field_class = marshmallow.fields.Nested

    def _get_lazy_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        """Return extra keyword arguments to pass to lazy customization classes.

        Subclasses can override this to inject additional kwargs (e.g. target_path
        for internal relations). The default returns an empty dict.
        """
        del element  # unused in base class, but subclasses may use it
        return {}

    def _get_lazy_schema_class_attributes(self, element: dict[str, Any]) -> dict[str, Any]:
        """Return extra class attributes for dynamically created lazy schema subclasses.

        Subclasses can override this to inject additional class attributes (e.g.
        target_path for internal relations). The default returns an empty dict.
        """
        del element  # unused in base class, but subclasses may use it
        return {}

    @override
    def _get_properties(self, element: dict[str, Any], ignore_missing: bool = True) -> dict[str, Any]:
        """Get the properties for the recursive pid relation data type.

        Note: we can not introspect the target's schema at this point, so
        we return only the explicitly defined properties and do not want
        to fail on the lazy properties - that's why the default value of
        `ignore_missing` is `True`.
        """
        return super()._get_properties(element, ignore_missing=ignore_missing)

    @override
    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
        path_suffix: str = "",
        ignored_keys: set[str] | None = None,
    ) -> Any:
        """Create facets for the data type.

        Unlike create_mapping/create_json_schema/create_relations/create_ui_model,
        facet generation has no lazy/deferred variant - facet *names* must be
        known synchronously at build time (see RecordFacetsPreset/
        MetadataFacetsPreset). A lazy-pid-relation is only ever used for a
        self-referencing relation, whose target - this same model - is still
        being built and so can never be introspected yet at this point;
        rather than guessing (which could produce an invalid facet, e.g.
        aggregating on a text field with no keyword sub-field), always skip
        facet generation for this relation's 'keys' and log why.
        """
        log.warning(
            "Cannot generate facets for the pid-relation's 'keys' on %r "
            "- the target model %r could not be resolved (likely a "
            "self-referencing relation still being built).",
            path,
            self._get_relation_model(element),
        )
        return super().get_facet(
            path,
            element,
            nested_facets,
            facets,
            path_suffix,
            ignored_keys,
        )

    @override
    def create_mapping(self, element: dict[str, Any]) -> Mapping[str, Any]:
        """Create a mapping for the data type."""
        model = self._get_relation_model(element, must_exist=True)
        keys = element.get("keys", [])
        lazy_kwargs = self._get_lazy_properties(element)

        # super().create_mapping already returns the full container for this
        # element (type/dynamic/properties) - the lazily-resolved keys are
        # merged into its "properties", so the lazy object itself *is* the
        # mapping for this element, not just its "properties" value.
        return ReferenceMappingProperties(
            model,
            keys,
            filename="record-mapping-link",
            initial_content=super().create_mapping(element),
            **lazy_kwargs,
        )

    @override
    def create_json_schema(self, element: dict[str, Any]) -> Mapping[str, Any]:
        """Create a json schema for the data type."""
        model = self._get_relation_model(element, must_exist=True)
        keys = element.get("keys", [])
        lazy_kwargs = self._get_lazy_properties(element)

        return ReferenceJSONSchemaProperties(
            model,
            keys,
            filename="record-jsonschema-link",
            initial_content={
                **super().create_json_schema(element),
                "unevaluatedProperties": False,
            },
            **lazy_kwargs,
        )

    @override
    def create_marshmallow_schema(self, element: dict[str, Any]) -> type[marshmallow.Schema]:
        """Create a marshmallow schema for the data type."""
        model = self._get_relation_model(element, must_exist=True)
        keys = element.get("keys", [])
        schema_attrs = self._get_lazy_schema_class_attributes(element)

        return type(
            self.name,
            (ReferenceMarshmallowSchema,),
            {
                "model": model,
                "keys": keys,
                "initial_schema": super().create_marshmallow_schema(element)(),
                **schema_attrs,
            },
        )

    @override
    def create_ui_marshmallow_schema(self, element: dict[str, Any]) -> type[marshmallow.Schema]:
        """Create a UI marshmallow schema for the data type."""
        model = self._get_relation_model(element, must_exist=True)
        keys = element.get("keys", [])
        schema_attrs = self._get_lazy_schema_class_attributes(element)

        return type(
            self.name,
            (ReferenceUIMarshmallowSchema,),
            {
                "model": model,
                "keys": keys,
                "initial_schema": super().create_ui_marshmallow_schema(element)(),
                **schema_attrs,
            },
        )

    @override
    def create_ui_model(
        self,
        element: dict[str, Any],
        path: list[str],
    ) -> dict[str, Any]:
        """Create a UI model for the data type."""
        model = self._get_relation_model(element, must_exist=True)
        keys = element.get("keys", [])
        lazy_kwargs = self._get_lazy_properties(element)

        # super().create_ui_model already returns the full node for this
        # element (help/label/hint/input/children) - see create_mapping above
        # for why the lazy object itself is returned rather than nested under
        # a "children" key of a separately-built node.
        #
        # Unlike create_mapping/create_json_schema, create_ui_model's return
        # type can't be widened to Mapping[str, Any] without a wider ripple -
        # several other overrides (ObjectDataType, ArrayDataType, numbers.py,
        # strings.py) mutate the parent's returned dict in place. The lazy
        # object is never mutated by any caller, so the cast is safe.
        return cast(
            "dict[str, Any]",
            ReferenceUIModel(
                model,
                keys,
                filename="record-ui-model-link",
                initial_content=super().create_ui_model(element, path),
                **lazy_kwargs,
            ),
        )

    #
    # Relations
    #
    @override
    def _relation_pid_field(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> PIDFieldContext | LazyModelPIDFieldContext:
        """Get the PID field from the element.

        Unlike PIDRelation._relation_pid_field, also accepts a bare model
        name via 'model' (not just 'pid_field'/'record_cls') - needed for
        self-referencing relations, where the target model can't be imported
        yet at build time (see LazyModelPIDFieldContext).
        """
        if "pid_field" in element or "record_cls" in element:
            return super()._relation_pid_field(element, path)
        try:
            imported_model = obj_or_import_string(self._get_relation_model(element, must_exist=True)) # TODO: import_runtime_model
        except ImportError:
            return LazyModelPIDFieldContext(self._get_relation_model(element, must_exist=True))

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

    @override
    def create_relations(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> list[Customization]:
        """Create the relation customizations for the data type.

        The relation itself (e.g. "direct") can be registered right away -
        its own PID field/keys are known from `element`. But for a
        self-referencing relation, the *nested* relations living inside the
        copied 'keys' data (e.g. a vocabulary relation nested inside a
        multilingual field) can't be discovered yet: `_get_properties`
        introspects the target's real field tree (see
        PIDRelation._get_target_properties), and that target is this same
        model, which is still being built. Discovery of those nested
        relations is deferred to first real access, via AddLazyRelation/
        LazyRelationsField, by which point the model has finished building
        and registered - see LazyRelationsField's docstring.
        """
        relation_path = self._relation_path(element, path)
        relation_name = self._relation_name(element, path)
        pid_field = self._relation_pid_field(element, path)
        cache_key = self._relation_cache_key(element, path)
        key_names = self._relation_key_names(element, path)

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

        relations.append(
            AddLazyRelation(lambda: self._resolve_nested_relation_fields(element, path)),
        )
        return relations

    def _resolve_nested_relation_fields(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> dict[str, RelationBase]:
        """Materialize this relation's nested relation fields, called lazily."""
        fields: dict[str, RelationBase] = {}
        for customization in self._build_nested_relation_customizations(element, path):
            if not isinstance(customization, RelationFieldCustomization):
                continue
            for name, field in customization.build_relation_fields().items():
                if isinstance(field, RelationsField): # TODO: could use a comment
                    fields.update(field._fields)
                else:
                    fields[name] = field
        return fields

    def _build_nested_relation_customizations(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> list[Customization]:
        """Walk this relation's nested properties, collecting relation-registering customizations.

        Called lazily (see create_relations above), so `_get_properties`
        (with the model now fully built and registered) resolves the
        relation's 'keys' against the target's real field tree instead of
        falling back to plain "id"/"@v" keyword properties.
        """
        result: list[Customization] = []
        for prop_name, prop in self._get_properties(element).items():
            result.extend(
                self._registry.get_type(prop).create_relations(
                    prop,
                    [*path, (prop_name, prop)],
                ),
            )
        return result
