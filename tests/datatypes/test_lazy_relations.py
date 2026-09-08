#
# Copyright (c) 2026 University of West Bohemia
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Unit tests for LazyPIDRelation._relation_pid_field and .create_relations.

These call the two methods directly against a registered "lazy-pid-relation"
datatype, with plain dicts standing in for a build-time element/path - no
mocks, and no need to actually build/register a full model.
"""

from __future__ import annotations

from typing import Any

import pytest

from oarepo_model.customizations.base import Customization
from oarepo_model.customizations.high_level.add_pid_relation import AddLazyRelation, AddPIDRelation
from oarepo_model.datatypes.base import DataType
from oarepo_model.datatypes.lazy_relations import LazyModelPIDFieldContext, LazyPIDRelation


class NoopCustomization(Customization):
    """A Customization that is neither AddPIDRelation nor AddLazyRelation.

    Used below to exercise the "skip customizations that aren't relation
    fields" branch of the nested-relation resolver built by
    LazyPIDRelation.create_relations - no such customization is ever
    actually produced by any relation-like datatype in this codebase today
    (they all only ever yield AddPIDRelation/AddLazyRelation), so a minimal
    real one is defined here instead of mocking one.
    """


class NoopRelationDataType(DataType):
    """A DataType whose create_relations yields a non-relation-field Customization."""

    TYPE = "noop-relation-for-test"

    def create_relations(
        self,
        element: dict[str, Any],  # noqa: ARG002
        path: list[tuple[str, dict[str, Any]]],  # noqa: ARG002
    ) -> list[Customization]:
        """Return a single Customization that is not a RelationFieldCustomization."""
        return [NoopCustomization("noop")]


@pytest.fixture
def lazy_pid_relation(datatype_registry) -> LazyPIDRelation:
    datatype_registry.add_types({"noop-relation-for-test": NoopRelationDataType})
    return datatype_registry.get_type({"type": "lazy-pid-relation"})


# ---------------------------------------------------------------------------
# _relation_pid_field
# ---------------------------------------------------------------------------


def test_relation_pid_field_with_pid_field_delegates_to_super(lazy_pid_relation):
    def _pid_field_getter(_element: dict[str, Any]) -> str:
        return "the-pid-field"

    element = {"pid_field": _pid_field_getter, "keys": []}
    assert lazy_pid_relation._relation_pid_field(element, []) == "the-pid-field"  # noqa: SLF001


def test_relation_pid_field_with_record_cls_delegates_to_super(lazy_pid_relation):
    class DummyRecord:
        pid = object()

    element = {"record_cls": DummyRecord, "keys": []}
    assert lazy_pid_relation._relation_pid_field(element, []) is DummyRecord.pid  # noqa: SLF001


def test_relation_pid_field_resolves_importable_model_object(lazy_pid_relation):
    # obj_or_import_string returns a non-string, truthy 'model' value as-is
    # (see invenio_base.utils.obj_or_import_string) - this stands in for a
    # 'model' given as an already-importable dotted path resolving to a real
    # (already built) target model namespace.
    class DummyRecord:
        pid = object()

    class DummyModelNamespace:
        Record = DummyRecord

    element = {"model": DummyModelNamespace, "keys": []}
    assert lazy_pid_relation._relation_pid_field(element, []) is DummyRecord.pid  # noqa: SLF001


def test_relation_pid_field_raises_when_model_object_has_no_pid_record(lazy_pid_relation):
    element = {"model": object(), "keys": []}  # a plain object has no .Record
    with pytest.raises(ValueError, match="does not have a 'pid' attribute"):
        lazy_pid_relation._relation_pid_field(element, [])  # noqa: SLF001


def test_relation_pid_field_raises_when_model_cannot_be_resolved(lazy_pid_relation):
    # A falsy, non-string 'model' makes obj_or_import_string return None
    # without raising ImportError - this is the "imported_model is None"
    # guard, as opposed to a bare unresolvable model *name* (a string),
    # which instead falls back to LazyModelPIDFieldContext (see the next
    # test) - obj_or_import_string only calls import_string for strings.
    element = {"model": 0, "keys": []}
    with pytest.raises(ValueError, match="could not be imported"):
        lazy_pid_relation._relation_pid_field(element, [])  # noqa: SLF001


def test_relation_pid_field_falls_back_to_lazy_context_for_bare_model_name(lazy_pid_relation):
    element = {"model": "some_self_referencing_model", "keys": []}
    pid_field = lazy_pid_relation._relation_pid_field(element, [])  # noqa: SLF001
    assert isinstance(pid_field, LazyModelPIDFieldContext)
    assert pid_field.model_name == "some_self_referencing_model"


# ---------------------------------------------------------------------------
# create_relations
# ---------------------------------------------------------------------------


def test_create_relations_registers_the_relation_itself(lazy_pid_relation):
    element = {"model": "some_self_referencing_model", "keys": ["id"]}
    relations = lazy_pid_relation.create_relations(element, [("direct", element)])

    assert len(relations) == 2
    add_pid_relation, add_lazy_relation = relations
    assert isinstance(add_pid_relation, AddPIDRelation)
    assert add_pid_relation.name == "direct"
    assert add_pid_relation.keys == ["id"]
    assert isinstance(add_pid_relation.pid_field, LazyModelPIDFieldContext)
    assert isinstance(add_lazy_relation, AddLazyRelation)


def test_create_relations_nested_resolver_skips_non_relation_field_customizations(lazy_pid_relation):
    element = {
        "model": "some_self_referencing_model",
        "keys": [{"myfield": {"type": "noop-relation-for-test"}}],
    }
    _, add_lazy_relation = lazy_pid_relation.create_relations(element, [("direct", element)])

    # NoopRelationDataType.create_relations (registered by the fixture)
    # contributes a plain Customization for "myfield", not a
    # RelationFieldCustomization - the resolver must skip it rather than
    # fail, and must not surface a relation field for it.
    fields = add_lazy_relation.resolver()
    assert fields == {}


def test_create_relations_nested_resolver_flattens_nested_lazy_relation_fields(lazy_pid_relation):
    # a relation nested inside another relation's 'keys' - its own
    # create_relations yields *both* an AddPIDRelation (for itself) and an
    # AddLazyRelation (for whatever might be nested inside *its* 'keys').
    element = {
        "model": "some_self_referencing_model",
        "keys": [
            {
                "nested": {
                    "type": "lazy-pid-relation",
                    "model": "some_self_referencing_model",
                    "keys": ["id"],
                },
            },
        ],
    }
    _, add_lazy_relation = lazy_pid_relation.create_relations(element, [("direct", element)])
    fields = add_lazy_relation.resolver()

    # the nested AddPIDRelation contributes a plain RelationBase field ...
    assert "direct.nested" in fields
    # ... while the nested AddLazyRelation contributes a RelationsField
    # group - resolving it (here empty, since "nested"'s only key is "id")
    # must not raise and must not add anything beyond the fields checked
    # above (its _fields get flattened into the outer dict, not nested).
    assert set(fields) == {"direct.nested"}
