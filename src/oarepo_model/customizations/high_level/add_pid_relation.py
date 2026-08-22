#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""High-level customization for adding PID relations to models.

This module provides the AddPIDRelation customization that creates appropriate
PID relation system fields based on the path structure. It supports simple
relations, list relations, and nested list relations by analyzing the presence
and position of array items in the relation path.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, override

from invenio_records.systemfields import SystemField
from invenio_records.systemfields.relations import RelationBase, RelationsField
from invenio_records_resources.records.systemfields import (
    PIDListRelation,
    PIDNestedListRelation,
    PIDRelation,
)
from oarepo_runtime.records.systemfields.relations import PIDArbitraryNestedListRelation
from werkzeug.utils import cached_property

from ..base import Customization

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from invenio_records_resources.records.systemfields.pid import PIDFieldContext

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class ARRAY_PATH_ITEM:  # noqa: N801
    """Marker for array items in the path.

    This class is used to indicate that a part of the path is an array item.
    It is used to differentiate between simple relations and list relations.
    """


def merge_paths_between_arrays(
    path: list[str | type[ARRAY_PATH_ITEM]],
) -> tuple[str | None, list[str]]:
    """Merge path segments between array markers.

    This function processes the path to identify segments between array markers
    and merges them into dot-separated strings. It also determines the relation
    field (the segment after the last array marker) if it exists.

    A free function (rather than an AddPIDRelation method) so it can also be
    used by AddInternalRelation.build_relation_fields, which needs the same
    array/relation-field split for InternalRelation but isn't an
    AddPIDRelation itself.
    """
    merged_paths_with_array_markers: list[Any] = []
    joined: list[str] = []
    for x in path:
        if isinstance(x, str):
            joined.append(x)
        else:
            if joined:
                merged_paths_with_array_markers.append(".".join(joined))
                joined = []
            merged_paths_with_array_markers.append(ARRAY_PATH_ITEM)
    if joined:
        merged_paths_with_array_markers.append(".".join(joined))

    # pop the relation field if the last item is not an array
    relation_field = (
        None if merged_paths_with_array_markers[-1] is ARRAY_PATH_ITEM else merged_paths_with_array_markers.pop()
    )

    # filter out array markers
    array_paths = [x for x in merged_paths_with_array_markers if x is not ARRAY_PATH_ITEM]

    return relation_field, array_paths


class RelationFieldCustomization(Customization, ABC):
    """Base class for customizations that contribute to the model's 'relations' dict.

    Factors out the {name: RelationBase | RelationsField} construction from
    `apply()` so it can also be reused by AddLazyRelation's deferred
    resolver, which needs the same result without a builder being available
    (see LazyRelationsField). RelationsField is included because that's what
    MultiRelationsField.__init__ itself accepts for nested groups (see its
    `isinstance(f, RelationBase) or isinstance(f, RelationsField)` assert) -
    AddLazyRelation is exactly such a nested group.
    """

    @abstractmethod
    def build_relation_fields(self) -> Mapping[str, RelationBase | RelationsField]:
        """Build and return the {name: field} entries this customization contributes."""

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        relations = builder.get_dictionary("relations")
        relations.update(self.build_relation_fields())


class AddPIDRelation(RelationFieldCustomization):
    """Customization to add PID relations to the model."""

    def __init__(
        self,
        name: str,
        path: list[str | type[ARRAY_PATH_ITEM]],
        keys: list[str],
        pid_field: PIDFieldContext,
        cache_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the AddPIDRelation customization.

        :param path: The path to the relation.
        :param keys: The keys for the relation.
        """
        super().__init__("add_pid_relation")
        self.name = name
        self.path = path
        self.keys = keys
        self.pid_field = pid_field
        self.cache_key = cache_key
        self.kwargs = kwargs

    @override
    def build_relation_fields(self) -> Mapping[str, RelationBase | RelationsField]:
        array_count = self.path.count(ARRAY_PATH_ITEM)

        relation_field, array_paths = merge_paths_between_arrays(self.path)

        match array_count:
            case 0:
                relation: RelationBase = PIDRelation(
                    relation_field,
                    keys=self.keys,
                    pid_field=self.pid_field,
                    cache_key=self.cache_key,
                    **self.kwargs,
                )
            case 1:
                # If the last element is an array, we create a PIDListRelation
                relation = PIDListRelation(
                    array_paths[0],
                    keys=self.keys,
                    pid_field=self.pid_field,
                    cache_key=self.cache_key,
                    relation_field=relation_field,
                    **self.kwargs,
                )
            case 2:
                if relation_field:
                    # invenio can not handle 2 arrays with a relation field at the end
                    # for that we use the arbitrary nested list relation that can do it
                    # albeit with a bit less efficiency
                    relation = PIDArbitraryNestedListRelation(
                        array_paths=array_paths,
                        relation_field=relation_field,
                        keys=self.keys,
                        pid_field=self.pid_field,
                        cache_key=self.cache_key,
                        **self.kwargs,
                    )
                else:
                    relation = PIDNestedListRelation(
                        array_paths[0],
                        relation_field=array_paths[1],
                        keys=self.keys,
                        pid_field=self.pid_field,
                        cache_key=self.cache_key,
                        **self.kwargs,
                    )
            case _:
                relation = PIDArbitraryNestedListRelation(
                    array_paths=array_paths,
                    relation_field=relation_field,
                    keys=self.keys,
                    pid_field=self.pid_field,
                    cache_key=self.cache_key,
                    **self.kwargs,
                )
        return {self.name: relation}


class LazyRelationsField(RelationsField):
    """A RelationsField group whose member fields are resolved on first real use.

    Used for relations nested inside a self-referencing pid-relation's copied
    'keys' (e.g. a vocabulary relation nested inside a multilingual field) -
    the target model is the model currently being built, so its real field
    tree can only be introspected once that model has finished building and
    been registered (see PIDRelation._get_target_properties). Resolution is
    deferred to first access of `_fields`, which - because `_fields` is
    itself a cached_property only ever touched from `MultiRelationsField`'s
    own `_fields`/`obj()` on the first real `record.relations` access - is
    guaranteed to happen well after that point (see field.py:42-45, 131-144
    and mapping.py:17-18 for the access chain this relies on).
    """

    def __init__(self, resolver: Callable[[], dict[str, RelationBase]]) -> None:
        """Initialize with a resolver, deferring RelationsField's own eager checks.

        Deliberately does not call RelationsField.__init__/super().__init__ -
        there are no real fields yet to satisfy its eager
        `assert all(isinstance(f, RelationBase) for f in fields.values())`,
        only a resolver that will produce them later.
        """
        SystemField.__init__(self)
        self._original_fields: dict[str, RelationBase] = {}
        self._resolver = resolver

    @cached_property
    def _fields(self) -> dict[str, RelationBase]:
        """Resolve the real relation fields, once, on first access."""
        return self._resolver()


class AddLazyRelation(RelationFieldCustomization):
    """Customization that adds a lazily-resolved group of relations to the model.

    Used in place of AddPIDRelation/statically walking a pid-relation's
    nested schema (see PIDRelation.create_relations) when the target model
    can't be introspected yet (self-referencing relations) - the whole
    nested-relation-discovery walk is deferred to first actual use via
    LazyRelationsField, by which point the target model is fully built and
    registered.
    """

    def __init__(self, resolver: Callable[[], dict[str, RelationBase]]) -> None:
        """Initialize with the resolver LazyRelationsField will call lazily.

        The name under which the resulting LazyRelationsField is registered
        in the model's 'relations' dict is auto-generated and never exposed
        to users - it only exists so MultiRelationsField's merge logic
        (field.py:131-144) has a dict key to iterate, and must never collide
        with a real, settable relation name, since MultiRelationsField.__set__
        (field.py:152-157) routes dict-style `record.relations = {...}`
        assignments by name.
        """
        super().__init__(f"__lazy_relations__{uuid.uuid4().hex}")
        self.resolver = resolver

    @override
    def build_relation_fields(self) -> Mapping[str, RelationBase | RelationsField]:
        return {self.name: LazyRelationsField(self.resolver)}
