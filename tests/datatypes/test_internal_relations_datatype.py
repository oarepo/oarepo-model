#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Pure unit tests for datatypes/internal_relations.py's building blocks.

Unlike tests/api_tests/test_internal_relations.py (which builds real models
and exercises them end-to-end, including through the service/search layer),
these tests call the module's helper functions/methods directly - most of
them need neither a Flask app nor a built model - to cover edge cases (a
malformed/nonexistent target_path, an explicit 'properties' escape hatch, a
missing 'target' key, ...) that the happy-path end-to-end tests never exercise.
"""

# ruff: noqa: SLF001 - reaching into private members is the point of this file

from __future__ import annotations

import marshmallow as ma
import pytest

from oarepo_model.customizations.high_level.add_internal_relation import AddInternalRelation
from oarepo_model.datatypes.internal_relations import (
    InternalRelationDataType,
    LazyProxiedInternalMarshmallowSchema,
    _unwrap_nested_field,
    _walk_mapping_path,
    _walk_type_tree_path,
    _walk_ui_model_path,
)


@pytest.fixture
def internal_relation_type(datatype_registry) -> InternalRelationDataType:
    """Return the real (registry-resolved, not mocked) InternalRelationDataType instance."""
    return datatype_registry.get_type("internal-relation")


# -- _walk_type_tree_path ----------------------------------------------------


def test_walk_type_tree_path_missing_segment_returns_none():
    assert _walk_type_tree_path({"a": {"type": "object", "properties": {}}}, "a.b") is None


def test_walk_type_tree_path_non_dict_node_returns_none():
    assert _walk_type_tree_path({"a": "not-a-dict"}, "a") is None


def test_walk_type_tree_path_array_without_dict_items_returns_none():
    assert _walk_type_tree_path({"a": {"type": "array", "items": "not-a-dict"}}, "a") is None


def test_walk_type_tree_path_none_root_returns_none():
    assert _walk_type_tree_path(None, "a") is None


def test_walk_type_tree_path_resolves_through_object_and_array_nesting():
    root = {
        "a": {
            "type": "object",
            "properties": {
                "b": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"c": {"type": "string"}},
                    },
                },
            },
        },
    }
    assert _walk_type_tree_path(root, "a.b") == {"c": {"type": "string"}}


# -- _walk_mapping_path -------------------------------------------------------


def test_walk_mapping_path_missing_segment_returns_none():
    assert _walk_mapping_path({}, "a") is None


def test_walk_mapping_path_non_dict_node_returns_none():
    assert _walk_mapping_path({"a": "not-a-dict"}, "a") is None


def test_walk_mapping_path_resolves_a_repeated_field_the_same_as_a_single_one():
    # OpenSearch mappings have no separate array type - a "proteins" array
    # field is mapped exactly like a single "protein" object would be.
    root = {"a": {"properties": {"b": {"type": "keyword"}}}}
    assert _walk_mapping_path(root, "a") == {"b": {"type": "keyword"}}


# -- _walk_ui_model_path -------------------------------------------------------


def test_walk_ui_model_path_missing_segment_returns_none():
    assert _walk_ui_model_path({}, "a") is None


def test_walk_ui_model_path_non_dict_node_returns_none():
    assert _walk_ui_model_path({"a": "not-a-dict"}, "a") is None


def test_walk_ui_model_path_child_wrapped_node_not_a_dict_returns_none():
    assert _walk_ui_model_path({"a": {"child": "not-a-dict"}}, "a") is None


def test_walk_ui_model_path_unwraps_child_for_array_shaped_nodes():
    # An array-shaped ui model node nests via "child" (wrapping a single
    # node with its own "children") instead of "children" directly.
    root = {"a": {"child": {"children": {"b": {"input": "keyword"}}}}}
    assert _walk_ui_model_path(root, "a") == {"b": {"input": "keyword"}}


# -- _unwrap_nested_field ------------------------------------------------------


def test_unwrap_nested_field_plain_non_nested_field_returns_none():
    assert _unwrap_nested_field(ma.fields.Str()) is None


def test_unwrap_nested_field_none_field_returns_none():
    assert _unwrap_nested_field(None) is None


def test_unwrap_nested_field_list_wrapping_non_nested_returns_none():
    assert _unwrap_nested_field(ma.fields.List(ma.fields.Str())) is None


def test_unwrap_nested_field_nested_field_is_returned_as_is():
    nested = ma.fields.Nested(ma.Schema.from_dict({}))
    assert _unwrap_nested_field(nested) is nested


def test_unwrap_nested_field_list_wrapping_nested_is_unwrapped():
    nested = ma.fields.Nested(ma.Schema.from_dict({}))
    assert _unwrap_nested_field(ma.fields.List(nested)) is nested


# -- LazyProxiedInternalMarshmallowSchema._descend -----------------------------


@pytest.fixture
def schema_with_nested_and_plain_fields() -> ma.Schema:
    inner = ma.Schema.from_dict({"title": ma.fields.Str()})
    return ma.Schema.from_dict({"sub": ma.fields.Nested(inner), "plain": ma.fields.Str()})()


def test_descend_missing_field_returns_none(schema_with_nested_and_plain_fields):
    assert LazyProxiedInternalMarshmallowSchema._descend(schema_with_nested_and_plain_fields, "missing") is None


def test_descend_non_nested_field_returns_none(schema_with_nested_and_plain_fields):
    assert LazyProxiedInternalMarshmallowSchema._descend(schema_with_nested_and_plain_fields, "plain") is None


def test_descend_descends_into_a_real_nested_field(schema_with_nested_and_plain_fields):
    result = LazyProxiedInternalMarshmallowSchema._descend(schema_with_nested_and_plain_fields, "sub")
    assert isinstance(result, ma.Schema)
    assert "title" in result.fields


# -- LazyProxiedInternalMarshmallowSchema._resolve_field -----------------------


def test_resolve_field_none_target_schema_returns_none():
    assert LazyProxiedInternalMarshmallowSchema._resolve_field(None, ["id"]) is None


def test_resolve_field_missing_single_part_key_returns_none(schema_with_nested_and_plain_fields):
    result = LazyProxiedInternalMarshmallowSchema._resolve_field(schema_with_nested_and_plain_fields, ["missing"])
    assert result is None


def test_resolve_field_intermediate_part_not_nested_returns_none(schema_with_nested_and_plain_fields):
    result = LazyProxiedInternalMarshmallowSchema._resolve_field(schema_with_nested_and_plain_fields, ["plain", "x"])
    assert result is None


def test_resolve_field_intermediate_part_missing_returns_none(schema_with_nested_and_plain_fields):
    result = LazyProxiedInternalMarshmallowSchema._resolve_field(
        schema_with_nested_and_plain_fields,
        ["missing", "x"],
    )
    assert result is None


def test_resolve_field_resolves_a_multi_part_dotted_key(schema_with_nested_and_plain_fields):
    field = LazyProxiedInternalMarshmallowSchema._resolve_field(schema_with_nested_and_plain_fields, ["sub", "title"])
    assert isinstance(field, ma.fields.Str)


def test_resolve_field_resolves_a_single_part_key(schema_with_nested_and_plain_fields):
    field = LazyProxiedInternalMarshmallowSchema._resolve_field(schema_with_nested_and_plain_fields, ["plain"])
    assert isinstance(field, ma.fields.Str)


# -- LazyProxiedInternalMarshmallowSchema._create_proxied_marshmallow ----------


class _StubProxiedSchema(LazyProxiedInternalMarshmallowSchema):
    """A concrete LazyProxiedInternalMarshmallowSchema whose target schema is hand-built.

    Avoids needing a real built/registered model just to exercise
    _create_proxied_marshmallow's dotted-key tree-building - `keys` includes a
    dotted "sub.title" entry so the nested dict branch of the tree-building
    loop actually runs. Not a test-grouping class - a genuine (if minimal)
    subclass of the production LazyProxiedInternalMarshmallowSchema, needed
    because that base class is abstract (_get_target_schema raises by default).
    """

    target_path = "container"
    keys: list[str] = ["id", "sub.title"]  # noqa: RUF012

    @classmethod
    def _get_target_schema(cls) -> ma.Schema:
        inner = ma.Schema.from_dict({"title": ma.fields.Str()})
        container = ma.Schema.from_dict({"id": ma.fields.Str(), "sub": ma.fields.Nested(inner)})
        return ma.Schema.from_dict({"container": ma.fields.Nested(container)})()


def test_create_proxied_marshmallow_resolves_dotted_keys():
    """_create_proxied_marshmallow should build a nested schema for a dotted 'keys' entry."""
    schema_cls = _StubProxiedSchema._create_proxied_marshmallow()
    dumped = schema_cls().dump({"id": "p1", "sub": {"title": "T"}})
    assert dumped == {"id": "p1", "sub": {"title": "T"}}


class _StubProxiedSchemaMissingKey(LazyProxiedInternalMarshmallowSchema):
    """A concrete LazyProxiedInternalMarshmallowSchema with a 'keys' entry that never resolves."""

    target_path = "container"
    keys: list[str] = ["nonexistent"]  # noqa: RUF012

    @classmethod
    def _get_target_schema(cls) -> ma.Schema:
        container = ma.Schema.from_dict({"id": ma.fields.Str()})
        return ma.Schema.from_dict({"container": ma.fields.Nested(container)})()


def test_create_proxied_marshmallow_missing_key_uses_missing_field_fallback():
    """An unresolvable 'keys' entry should fall back to _missing_field (default: raises)."""
    with pytest.raises(KeyError):
        _StubProxiedSchemaMissingKey._create_proxied_marshmallow()


# -- InternalRelationDataType._target_path / ._model ---------------------------


def test_target_path_raises_when_target_is_missing(internal_relation_type):
    """_target_path should raise a clear error when the required 'target' key is absent."""
    with pytest.raises(ValueError, match="'target' key is required"):
        internal_relation_type._target_path({})


def test_model_raises_outside_a_build(internal_relation_type):
    """_model should raise when called outside of a model build (api.current_model unset)."""
    with pytest.raises(RuntimeError, match="current_model is not set"):
        internal_relation_type._model()


# -- InternalRelationDataType._get_properties -----------------------------------


def test_get_properties_explicit_properties_are_returned_as_is(internal_relation_type):
    properties = {"id": {"type": "keyword"}, "name": {"type": "keyword"}}
    assert internal_relation_type._get_properties({"properties": properties}) is properties


def test_get_properties_non_dict_explicit_properties_raises(internal_relation_type):
    with pytest.raises(TypeError, match="Expected 'properties' to be a dict"):
        internal_relation_type._get_properties({"properties": ["not", "a", "dict"]})


def test_get_properties_string_keys_fall_back_to_keyword(internal_relation_type):
    ret = internal_relation_type._get_properties({"target": "metadata.proteins", "keys": ["id", "name"]})
    assert ret["id"] == {"type": "keyword"}
    assert ret["name"] == {"type": "keyword"}
    assert ret["@v"] == {"type": "keyword", "skip_marshmallow": True}


def test_get_properties_dict_shaped_key_entries_are_honored(internal_relation_type):
    ret = internal_relation_type._get_properties(
        {"target": "metadata.proteins", "keys": [{"id": {"type": "keyword"}}, {"amount": {"type": "int"}}]},
    )
    assert ret["amount"] == {"type": "int"}
    # "id" is always synthesized if missing - here it is explicitly given instead.
    assert ret["id"] == {"type": "keyword"}


def test_get_properties_invalid_key_type_raises(internal_relation_type):
    with pytest.raises(TypeError, match="Invalid key type"):
        internal_relation_type._get_properties({"target": "metadata.proteins", "keys": [123]})


def test_get_properties_id_and_marker_are_synthesized_when_absent_from_keys(internal_relation_type):
    ret = internal_relation_type._get_properties({"target": "metadata.proteins", "keys": ["name"]})
    assert ret["id"] == {"type": "keyword"}
    assert ret["@v"] == {"type": "keyword", "skip_marshmallow": True}


# -- InternalRelationDataType.get_facet (explicit 'properties' eager branch) ---


@pytest.fixture
def element_with_explicit_properties() -> dict:
    return {
        "target": "metadata.proteins",
        "properties": {
            "id": {"type": "keyword"},
            "name": {"type": "keyword"},
            "@v": {"type": "keyword", "skip_marshmallow": True},
        },
    }


def test_get_facet_generates_a_facet_per_property_and_skips_the_version_marker(
    internal_relation_type,
    element_with_explicit_properties,
):
    facets: dict[str, list] = {}
    result = internal_relation_type.get_facet(
        "metadata.primary_protein",
        element_with_explicit_properties,
        [],
        facets,
    )
    assert result is facets
    assert "metadata.primary_protein.id" in facets
    assert "metadata.primary_protein.name" in facets
    assert "metadata.primary_protein.@v" not in facets


def test_get_facet_empty_path_uses_the_bare_key_as_facet_name(
    internal_relation_type,
    element_with_explicit_properties,
):
    facets: dict[str, list] = {}
    internal_relation_type.get_facet("", element_with_explicit_properties, [], facets)
    assert "id" in facets
    assert "name" in facets


def test_get_facet_path_already_ending_with_key_is_reused_unchanged(internal_relation_type):
    facets: dict[str, list] = {}
    element = {"target": "metadata.proteins", "properties": {"id": {"type": "keyword"}}}
    internal_relation_type.get_facet("metadata.primary_protein.id", element, [], facets)
    assert "metadata.primary_protein.id" in facets
    # the endswith() branch reuses `path` unchanged rather than doubling
    # the "id" suffix - a wrong implementation would produce this key too.
    assert "metadata.primary_protein.id.id" not in facets


# -- InternalRelationDataType.create_relations (explicit 'properties' branch) --


def test_create_relations_discovers_customizations_for_explicit_properties(internal_relation_type):
    """create_relations's 'properties' branch should walk the explicit properties for nested relations."""
    element = {
        "target": "metadata.proteins",
        "keys": ["id", "name"],
        "properties": {
            "id": {"type": "keyword"},
            "name": {"type": "keyword"},
        },
    }
    path = [("metadata", {}), ("primary_protein", element)]

    customizations = internal_relation_type.create_relations(element, path)

    # Exactly the field's own AddInternalRelation - "id"/"name" are plain
    # keyword properties, so _discover_nested_relation_customizations's walk
    # over them contributes no further customizations.
    assert len(customizations) == 1
    assert isinstance(customizations[0], AddInternalRelation)
    assert customizations[0].name == "metadata.primary_protein"
    assert customizations[0].target_path == "metadata.proteins"
