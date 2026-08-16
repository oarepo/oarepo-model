#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""High-level customization for adding internal (same-record) relations to models.

This module provides the AddInternalRelation customization that creates an
`oarepo_runtime.records.systemfields.relations.InternalRelation` system field -
a relation that resolves against a part of the *same* record (via its
`InternalRelations` lookup table system field) instead of an externally
PID-resolved record. See datatypes/internal_relations.py for the data type that
generates these customizations, and ir.md for the overall design/TODO list.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_runtime.records.systemfields.relations import InternalRelation

from .add_pid_relation import ARRAY_PATH_ITEM, RelationFieldCustomization, merge_paths_between_arrays

if TYPE_CHECKING:
    from collections.abc import Mapping

    from invenio_records.systemfields.relations import RelationBase


class AddInternalRelation(RelationFieldCustomization):
    """Customization to add an internal (same-record) relation to the model."""

    def __init__(
        self,
        name: str,
        path: list[str | type[ARRAY_PATH_ITEM]],
        keys: list[str],
        target_paths: list[str],
        **kwargs: Any,
    ) -> None:
        """Initialize the AddInternalRelation customization.

        :param name: The name the relation is registered under in the model's
            'relations' dict (and, transitively, on `record.relations`).
        :param path: The path to the relation, in the same shape AddPIDRelation
            expects (see relation_path_from_customization_path).
        :param keys: The keys to embed from the resolved target.
        :param target_paths: The record-relative paths InternalRelation looks the
            relation's ids up against (see oarepo_runtime's InternalRelations
            system field - it must be configured with a superset of these paths).
        """
        super().__init__("add_internal_relation")
        self.name = name
        self.path = path
        self.keys = keys
        self.target_paths = target_paths
        self.kwargs = kwargs

    @override
    def build_relation_fields(self) -> Mapping[str, RelationBase]:
        relation_field, array_paths = merge_paths_between_arrays(self.path)

        # InternalRelation extends oarepo_runtime's ArbitraryPathRelation (not
        # invenio_records_resources's PIDRelation/PIDListRelation/PIDNestedListRelation),
        # which natively handles 0, 1 or arbitrarily many array levels via
        # array_paths/relation_field alone - unlike AddPIDRelation.build_relation_fields,
        # there is no need to branch on how many array markers were in the path.
        field: RelationBase = InternalRelation(
            array_paths=array_paths,
            relation_field=relation_field,
            target_paths=self.target_paths,
            keys=self.keys,
            **self.kwargs,
        )
        return {self.name: field}
