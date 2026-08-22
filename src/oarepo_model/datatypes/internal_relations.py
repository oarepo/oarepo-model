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

from typing import TYPE_CHECKING, Any, cast, override

from oarepo_model.api import current_model
from oarepo_model.customizations.high_level.add_internal_relation import AddInternalRelation
from oarepo_model.customizations.high_level.add_pid_relation import AddLazyRelation
from oarepo_model.utils import walk_type_tree_path

from .lazy_relations import LazyPIDRelation

if TYPE_CHECKING:
    from oarepo_model.customizations.base import Customization


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

    @override
    def _get_lazy_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        """Inject target_path as a kwarg to lazy customization classes."""
        return {"target_path": self._target_path(element)}

    @override
    def _get_lazy_schema_class_attributes(self, element: dict[str, Any]) -> dict[str, Any]:
        """Inject target_path as a class attribute for lazy schema subclasses."""
        return {"target_path": self._target_path(element)}

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

        PIDRelation._get_target_properties already resolves the target model
        (via self._get_relation_model, overridden above to mean "the model
        currently being built") down to its merged record/metadata root -
        this only needs to further descend that root to target_path.
        """
        root = super()._get_target_properties(element)
        return walk_type_tree_path(root, self._target_path(element)) or {}

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
