# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Corner cases tests for utils."""

from __future__ import annotations

import copy

import pytest

from oarepo_model.utils import (
    ReadOnlyDict,
    convert_to_python_identifier,
    deepcopy_to_plain,
    dump_to_json,
    readonly_dict_merger,
    title_case,
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
    assert d._data is not dc._data


def test_merge_read_only_dict():
    d = {
        "a": ReadOnlyDict({"a": 1, "b": 2}),
    }
    assert readonly_dict_merger.merge(d, {"a": {"c": 3}}) == {"a": {"a": 1, "b": 2, "c": 3}}


def test_merge_read_only_dict_nested():
    assert readonly_dict_merger.merge(ReadOnlyDict({"a": {"a": 1}}), {"a": {"c": 3}}) == {"a": {"a": 1, "c": 3}}


def test_merge_read_only_dict_list_tuple_is_appended():
    assert readonly_dict_merger.merge(ReadOnlyDict({"enum": ["a", "b"]}), {"enum": ["c"]}) == {"enum": ["a", "b", "c"]}
    assert readonly_dict_merger.merge(ReadOnlyDict({"enum": ("a", "b")}), {"enum": ["c"]}) == {"enum": ["a", "b", "c"]}


def test_deeply_copy_to_mutable_converts_mappings_and_sequences():
    leaf = "blah"
    source = ReadOnlyDict({"a": (1, 2), "b": ReadOnlyDict({"c": [leaf]}), "s": {"t": (leaf,)}})

    result = deepcopy_to_plain(source)

    assert result == {"a": [1, 2], "b": {"c": [leaf]}, "s": {"t": [leaf]}}
    assert type(result) is dict
    assert type(result["a"]) is list
    assert type(result["b"]) is dict
    assert type(result["s"]["t"]) is list


def test_deeply_copy_to_mutable_shares_leaves_and_leaves_source_intact():
    leaf = "blah"
    source = ReadOnlyDict({"a": ReadOnlyDict({"c": [leaf]})})

    result = deepcopy_to_plain(source)

    assert result["a"]["c"][0] is leaf
    assert isinstance(source, ReadOnlyDict)
    assert isinstance(source["a"], ReadOnlyDict)
    assert type(source["a"]["c"]) is list


def test_deeply_copy_to_mutable_passes_through_other_values():
    assert deepcopy_to_plain(5) == 5
    assert deepcopy_to_plain("x") == "x"
    assert deepcopy_to_plain(None) is None

    a_tuple = (1, 2)
    assert type(deepcopy_to_plain(a_tuple)) is list

    a_set = {1, 2}
    assert deepcopy_to_plain({"s": a_set})["s"] == a_set


NAMES = [
    "",
    "a",
    "a-b",
    "for",
    "2nd",
    "2 nd",
    "9",
    "-",
    "ID",
    "UIModel",
    "HTTPResponse",
    "ParentPIDProvider",
    "v1_0_0",
    "a.b/c",
    "日本語x",
]


def test_convert_to_python_identifier():
    assert convert_to_python_identifier("") == "_empty_"
    assert convert_to_python_identifier("a") == "a"
    assert convert_to_python_identifier("a-b") == "a_45_b"
    assert convert_to_python_identifier("for") == "for_"
    assert convert_to_python_identifier("2nd") == "_2nd"
    assert convert_to_python_identifier("2 nd") == "_2_32_nd"


def test_convert_to_python_identifier_always_returns_an_identifier():
    assert [x for x in NAMES if not convert_to_python_identifier(x).isidentifier()] == []


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("draft_test", "DraftTest"),
        ("DraftTest", "DraftTest"),
        ("Model", "Model"),
        ("UIModel", "UIModel"),
        ("ID", "ID"),
        ("HTTPResponse", "HTTPResponse"),
        ("ParentPIDProvider", "ParentPIDProvider"),
        ("parent_pid_provider", "ParentPidProvider"),
        ("v1_0_0", "V100"),
        ("2nd", "_2nd"),
        ("a.b/c", "ABC"),
    ],
)
def test_title_case(name, expected):
    assert title_case(name) == expected
    assert title_case(expected) == expected


def test_title_case_needs_something_to_case():
    with pytest.raises(ValueError, match="no letters or digits"):
        title_case("---")


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


def test_walk_type_tree_path_raises_for_a_non_object_leaf():
    root = {"a": {"type": "string"}}
    with pytest.raises(TypeError):
        walk_type_tree_path(root, "a")
