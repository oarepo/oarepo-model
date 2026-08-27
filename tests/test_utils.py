#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Corner cases tests for utils."""

from __future__ import annotations

import copy

import pytest

from oarepo_model.utils import (
    ReadOnlyDict,
    convert_to_python_identifier,
    dump_to_json,
    walk_type_tree_path,
    walk_type_tree_path_leaf,
)


def test_read_only_dict():
    d = ReadOnlyDict({"a": 1, "b": 2})
    assert d["a"] == 1
    assert d["b"] == 2
    assert len(d) == 2
    assert list(d) == ["a", "b"]
    assert repr(d) == "ReadOnlyDict({'a': 1, 'b': 2})"
    dc = copy.deepcopy(d)
    assert dc["a"] == 1
    assert dc["b"] == 2
    assert len(dc) == 2
    assert list(dc) == ["a", "b"]
    assert repr(dc) == "ReadOnlyDict({'a': 1, 'b': 2})"
    assert d is not dc
    assert d._data is not dc._data  # noqa: SLF001


def test_convert_to_python_identifier():
    assert convert_to_python_identifier("") == "_empty_"
    assert convert_to_python_identifier("a") == "a"
    assert convert_to_python_identifier("a-b") == "a_45_b"
    assert convert_to_python_identifier("for") == "for_"


def test_dump_to_json():
    assert dump_to_json({"a": 1}) == '{"a": 1}'
    assert dump_to_json({"a": 1, "b": 2}) == '{"a": 1, "b": 2}'
    assert dump_to_json(ReadOnlyDict({"a": 1, "b": 2})) == '{"a": 1, "b": 2}'

    with pytest.raises(TypeError, match=r"Object of type .* is not JSON serializable"):
        assert dump_to_json(object())


# A JSON Schema fragment shaped like PolymorphicDataType.create_json_schema's
# output for an array of polymorphic items: the array's "items" node has no
# "properties" of its own, only a "oneOf" list of per-variant branches.
_POLYMORPHIC_ARRAY_ROOT = {
    "entities": {
        "type": "array",
        "items": {
            "oneOf": [
                {
                    "type": "object",
                    "properties": {
                        "entity_type": {"type": "string", "const": "person"},
                        "id": {"type": "string"},
                        "first_name": {"type": "string"},
                    },
                },
                {
                    "type": "object",
                    "properties": {
                        "entity_type": {"type": "string", "const": "organization"},
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                    },
                },
            ],
        },
    },
}


def test_walk_type_tree_path_merges_oneof_branch_properties():
    # "id" is declared on both branches, "first_name"/"name" only on one each
    # - all three must resolve via the union of every oneOf branch.
    properties = walk_type_tree_path(_POLYMORPHIC_ARRAY_ROOT, "entities")
    assert properties == {
        "entity_type": {"type": "string", "const": "organization"},
        "id": {"type": "string"},
        "first_name": {"type": "string"},
        "name": {"type": "string"},
    }


def test_walk_type_tree_path_leaf_resolves_field_behind_polymorphic_array():
    assert walk_type_tree_path_leaf(_POLYMORPHIC_ARRAY_ROOT, "entities.id") == {"type": "string"}
    assert walk_type_tree_path_leaf(_POLYMORPHIC_ARRAY_ROOT, "entities.name") == {"type": "string"}


def test_walk_type_tree_path_does_not_mutate_or_alias_oneof_branches():
    # "id" differs between branches (one has an extra "format" key) so that a
    # merge which mutates the first branch's dict in place - instead of a
    # private copy - is actually observable, not silently identical.
    root = {
        "entities": {
            "type": "array",
            "items": {
                "oneOf": [
                    {"type": "object", "properties": {"id": {"type": "string"}, "first_name": {"type": "string"}}},
                    {
                        "type": "object",
                        "properties": {"id": {"type": "string", "format": "uuid"}, "name": {"type": "string"}},
                    },
                ],
            },
        },
    }
    branch1_properties = root["entities"]["items"]["oneOf"][0]["properties"]
    original_branch1_id = copy.deepcopy(branch1_properties["id"])

    merged = walk_type_tree_path(root, "entities")

    # the source tree must be untouched ...
    assert branch1_properties["id"] == original_branch1_id
    # ... and the returned mapping must not alias into it either.
    assert merged["first_name"] is not branch1_properties["first_name"]
    assert merged["id"] is not branch1_properties["id"]


def test_walk_type_tree_path_empty_when_oneof_branches_have_no_properties():
    # Mirrors a plain node with an explicit empty "properties": {} - resolves
    # to an (empty) properties mapping, not a failed lookup.
    root = {"a": {"type": "array", "items": {"oneOf": [{"type": "string"}]}}}
    assert walk_type_tree_path(root, "a") == {}


def test_walk_type_tree_path_returns_none_for_a_non_object_leaf():
    root = {"a": {"type": "string"}}
    assert walk_type_tree_path(root, "a") is None
