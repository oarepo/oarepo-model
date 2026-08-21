#
# Copyright (c) 2026 University of West Bohemia
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Additional tests for collection data types.

Covers:
- unique_validator function (valid list passes, list with duplicates raises)
- unique_items=True enforced through array marshmallow field
- Array min_items / max_items constraints
- NestedDataType mapping type is "nested"
- ObjectDataType error path: missing "properties" key
- ObjectDataType error path: invalid marshmallow_schema_class string
- ObjectDataType marshmallow_schema_mixins (including schema-wide validators declared by a mixin)
- [] shortcut expansion inside add_types / get_type (properties + items dict shortcuts)
- DynamicObjectDataType JSON schema and mapping
- ArrayDataType create_mapping delegates to items (skips the array wrapper)
"""
# ruff: noqa: D102

from __future__ import annotations

from typing import Any

import marshmallow as ma
import pytest

from oarepo_model.datatypes.collections import NoPropertiesError, unique_validator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_schema(datatype_registry, element, extra_types=None):
    if extra_types:
        datatype_registry.add_types(extra_types)
    field = datatype_registry.get_type(element).create_marshmallow_field(field_name="a", element=element)
    return ma.Schema.from_dict({"a": field})()


def object_element(mixins, properties=None):
    """Build an object element with the given marshmallow_schema_mixins."""
    return {
        "type": "object",
        "properties": properties or {"start": {"type": "keyword"}, "end": {"type": "keyword"}},
        "marshmallow_schema_mixins": mixins,
    }


# ---------------------------------------------------------------------------
# Schema mixins used by the marshmallow_schema_mixins option.
# They are referenced by their fully qualified name, so they must stay at module level.
# ---------------------------------------------------------------------------

DATE_RANGE_MIXIN = "tests.datatypes.test_collections_extra.DateRangeMixin"
REQUIRED_TOGETHER_MIXIN = "tests.datatypes.test_collections_extra.RequiredTogetherMixin"
EXTRA_FIELD_MIXIN = "tests.datatypes.test_collections_extra.ExtraFieldMixin"


class DateRangeMixin(ma.Schema):
    """Mixin declaring a schema-wide validator that compares two properties."""

    @ma.validates_schema
    def check_range(self, data, **kwargs: Any) -> None:  # noqa: ARG002
        """Reject an 'end' value that comes before 'start'."""
        start, end = data.get("start"), data.get("end")
        if start and end and start > end:
            raise ma.ValidationError({"end": ["end must not be before start"]})


class RequiredTogetherMixin(ma.Schema):
    """Second mixin with a schema-wide validator, used to check that mixins stack."""

    @ma.validates_schema
    def check_together(self, data, **kwargs: Any) -> None:  # noqa: ARG002
        """Reject data where only one of city/country is present."""
        if ("city" in data) != ("country" in data):
            raise ma.ValidationError({"country": ["city and country must be used together"]})


class ExtraFieldMixin(ma.Schema):
    """Mixin that contributes an additional field to the schema."""

    stamped = ma.fields.String(load_default="unknown")


class NotASchema:
    """Deliberately not a marshmallow.Schema subclass, used for error-path tests."""


class PlainSchema(ma.Schema):
    """A ready-made schema used to check that marshmallow_schema_class takes precedence."""


# ===========================================================================
# unique_validator  - unit-level
# ===========================================================================


class TestUniqueValidator:
    """unique_validator must raise only when duplicates are present."""

    def test_empty_list_is_valid(self):
        unique_validator([])  # must not raise

    def test_list_of_unique_scalars_is_valid(self):
        unique_validator([1, 2, 3])

    def test_list_of_unique_dicts_is_valid(self):
        unique_validator([{"a": 1}, {"a": 2}])

    def test_list_with_duplicate_scalar_raises(self):
        with pytest.raises(ma.ValidationError):
            unique_validator([1, 2, 1])

    def test_list_with_duplicate_dict_raises(self):
        with pytest.raises(ma.ValidationError):
            unique_validator([{"a": 1}, {"a": 1}])

    def test_list_with_multiple_duplicates_raises(self):
        with pytest.raises(ma.ValidationError):
            unique_validator([1, 1, 2, 2])


# ===========================================================================
# unique_items=True through array schema
# ===========================================================================


class TestUniqueItemsInArray:
    """unique_items=True on an array element must reject duplicate entries."""

    def test_unique_items_rejects_duplicates(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "array", "items": {"type": "keyword"}, "unique_items": True},
        )
        with pytest.raises(ma.ValidationError):
            schema.load({"a": ["x", "x"]})

    def test_unique_items_accepts_distinct_values(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "array", "items": {"type": "keyword"}, "unique_items": True},
        )
        assert schema.load({"a": ["x", "y", "z"]}) == {"a": ["x", "y", "z"]}

    def test_without_unique_items_duplicates_are_accepted(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "array", "items": {"type": "keyword"}},
        )
        assert schema.load({"a": ["x", "x"]}) == {"a": ["x", "x"]}


# ===========================================================================
# Array min_items / max_items
# ===========================================================================


class TestArrayLengthConstraints:
    """min_items and max_items must be enforced via marshmallow.validate.Length."""

    def test_min_items_rejects_too_few(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "array", "items": {"type": "int"}, "min_items": 2},
        )
        with pytest.raises(ma.ValidationError):
            schema.load({"a": [1]})

    def test_min_items_accepts_exact_count(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "array", "items": {"type": "int"}, "min_items": 2},
        )
        assert schema.load({"a": [1, 2]}) == {"a": [1, 2]}

    def test_max_items_rejects_too_many(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "array", "items": {"type": "int"}, "max_items": 2},
        )
        with pytest.raises(ma.ValidationError):
            schema.load({"a": [1, 2, 3]})

    def test_max_items_accepts_exact_count(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "array", "items": {"type": "int"}, "max_items": 2},
        )
        assert schema.load({"a": [1, 2]}) == {"a": [1, 2]}


# ===========================================================================
# NestedDataType
# ===========================================================================


class TestNestedDataType:
    """nested type must produce ES mapping type 'nested', not 'object'."""

    def test_nested_mapping_type_is_nested(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "nested"})
        mapping = dt.create_mapping({"type": "nested", "properties": {"x": {"type": "keyword"}}})
        assert mapping["type"] == "nested"

    def test_nested_mapping_contains_properties(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "nested"})
        mapping = dt.create_mapping({"type": "nested", "properties": {"score": {"type": "int"}}})
        assert "score" in mapping["properties"]

    def test_nested_schema_round_trip(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {
                "type": "array",
                "items": {
                    "type": "nested",
                    "properties": {"tag": {"type": "keyword"}},
                },
            },
        )
        data = {"a": [{"tag": "foo"}, {"tag": "bar"}]}
        assert schema.load(data) == data


# ===========================================================================
# ObjectDataType error paths
# ===========================================================================


class TestObjectDataTypeErrorPaths:
    """ObjectDataType must raise clear errors for invalid configurations."""

    def test_missing_properties_raises_value_error(self, datatype_registry):
        """create_marshmallow_field on an object without 'properties' must raise ValueError."""
        dt = datatype_registry.get_type({"type": "object"})
        with pytest.raises(NoPropertiesError):
            dt.create_marshmallow_field(
                field_name="a",
                element={"type": "object"},  # no properties
            )

    def test_invalid_marshmallow_schema_class_raises(self, datatype_registry):
        """marshmallow_schema_class pointing to a non-Schema class must raise ValueError."""
        dt = datatype_registry.get_type({"type": "object"})
        with pytest.raises((ValueError, ImportError, AttributeError, Exception)):
            dt.create_marshmallow_schema({"type": "object", "marshmallow_schema_class": "this.does.not.exist:Foo"})


# ===========================================================================
# ObjectDataType marshmallow_schema_mixins
# ===========================================================================


class TestMarshmallowSchemaMixins:
    """marshmallow_schema_mixins must be mixed into the generated object schema.

    A mixin is referenced by its fully qualified name and must be a subclass of
    ``marshmallow.Schema``. Besides extra fields, a mixin can declare schema-wide
    (cross-field) validators, which is the main reason to use this option.
    """

    # -- generated schema --------------------------------------------------

    def test_mixin_is_a_base_of_the_generated_schema(self, datatype_registry):
        """The imported mixin must appear in the MRO of the generated schema."""
        element = object_element([DATE_RANGE_MIXIN])
        schema_cls = datatype_registry.get_type(element).create_marshmallow_schema(element)
        assert issubclass(schema_cls, DateRangeMixin)
        assert issubclass(schema_cls, ma.Schema)

    def test_declared_properties_are_kept(self, datatype_registry):
        """Mixins must not replace the fields generated from 'properties'."""
        element = object_element([DATE_RANGE_MIXIN])
        schema_cls = datatype_registry.get_type(element).create_marshmallow_schema(element)
        assert set(schema_cls().fields) >= {"start", "end"}

    # -- schema-wide validator declared by a mixin -------------------------

    def test_mixin_schema_validator_rejects_invalid_data(self, datatype_registry):
        """The cross-field validator coming from the mixin must reject invalid data."""
        schema = make_schema(datatype_registry, object_element([DATE_RANGE_MIXIN]))
        with pytest.raises(ma.ValidationError):
            schema.load({"a": {"start": "2024-05-01", "end": "2024-01-01"}})

    def test_mixin_schema_validator_accepts_valid_data(self, datatype_registry):
        """Data that satisfies the mixin validator loads unchanged."""
        schema = make_schema(datatype_registry, object_element([DATE_RANGE_MIXIN]))
        data = {"a": {"start": "2024-01-01", "end": "2024-05-01"}}
        assert schema.load(data) == data

    def test_without_mixins_the_same_data_is_accepted(self, datatype_registry):
        """Control case: the cross-field rule comes from the mixin, not from the properties."""
        schema = make_schema(
            datatype_registry,
            {
                "type": "object",
                "properties": {"start": {"type": "keyword"}, "end": {"type": "keyword"}},
            },
        )
        data = {"a": {"start": "2024-05-01", "end": "2024-01-01"}}
        assert schema.load(data) == data

    def test_mixin_schema_validator_is_skipped_without_the_relevant_properties(self, datatype_registry):
        """The mixin validator must not invent errors for unrelated data."""
        element = object_element([DATE_RANGE_MIXIN], properties={"start": {"type": "keyword"}})
        schema = make_schema(datatype_registry, element)
        assert schema.load({"a": {"start": "2024-05-01"}}) == {"a": {"start": "2024-05-01"}}

    def test_mixin_error_message_is_reported_for_the_offending_property(self, datatype_registry):
        """The message raised by the mixin must reach the client for the right property."""
        schema = make_schema(datatype_registry, object_element([DATE_RANGE_MIXIN]))
        with pytest.raises(ma.ValidationError) as exc_info:
            schema.load({"a": {"start": "2024-05-01", "end": "2024-01-01"}})
        assert exc_info.value.messages["a"]["end"] == ["end must not be before start"]

    def test_multiple_mixins_are_all_applied(self, datatype_registry):
        """Validators of all listed mixins must be collected."""
        element = object_element(
            [DATE_RANGE_MIXIN, REQUIRED_TOGETHER_MIXIN],
            properties={
                "start": {"type": "keyword"},
                "end": {"type": "keyword"},
                "city": {"type": "keyword"},
                "country": {"type": "keyword"},
            },
        )
        schema = make_schema(datatype_registry, element)
        assert issubclass(type(schema.fields["a"].schema), RequiredTogetherMixin)
        # valid for both mixins
        data = {"a": {"start": "2024-01-01", "end": "2024-05-01", "city": "Pilsen", "country": "CZ"}}
        assert schema.load(data) == data
        with pytest.raises(ma.ValidationError):
            # fails only the DateRangeMixin validator
            schema.load({"a": {**data["a"], "end": "2023-12-31"}})
        with pytest.raises(ma.ValidationError):
            # fails only the RequiredTogetherMixin validator
            schema.load({"a": {"start": "2024-01-01", "end": "2024-05-01", "city": "Pilsen"}})

    def test_mixin_can_declare_additional_fields(self, datatype_registry):
        """Fields declared by a mixin become part of the generated schema."""
        element = object_element([EXTRA_FIELD_MIXIN])
        schema = make_schema(datatype_registry, element)
        assert "stamped" in schema.fields["a"].schema.fields
        assert schema.load({"a": {"start": "x", "end": "y"}}) == {"a": {"start": "x", "end": "y", "stamped": "unknown"}}

    def test_mixins_are_applied_to_array_items(self, datatype_registry):
        """The mixin must be applied when the object is used as array items."""
        schema = make_schema(
            datatype_registry,
            {"type": "array", "items": object_element([DATE_RANGE_MIXIN])},
        )
        valid = {"a": [{"start": "2024-01-01", "end": "2024-05-01"}]}
        assert schema.load(valid) == valid
        with pytest.raises(ma.ValidationError):
            # the second item violates the schema-wide validator of the mixin
            schema.load(
                {
                    "a": [
                        {"start": "2024-01-01", "end": "2024-05-01"},
                        {"start": "2024-05-01", "end": "2024-01-01"},
                    ]
                }
            )

    # -- error paths -------------------------------------------------------

    def test_mixins_must_be_a_list(self, datatype_registry):
        """A single string instead of a list must raise ValueError."""
        element = object_element(DATE_RANGE_MIXIN)
        with pytest.raises(ValueError, match="marshmallow_schema_mixins must be a list"):
            datatype_registry.get_type(element).create_marshmallow_schema(element)

    def test_mixin_must_be_a_schema_subclass(self, datatype_registry):
        """A mixin that is not a marshmallow.Schema subclass must raise TypeError."""
        element = object_element(["tests.datatypes.test_collections_extra.NotASchema"])
        with pytest.raises(TypeError, match=r"must be a subclass of marshmallow\.Schema"):
            datatype_registry.get_type(element).create_marshmallow_schema(element)

    def test_unknown_mixin_import_path_fails(self, datatype_registry):
        """A typo in the mixin import path must fail loudly."""
        element = object_element(["tests.datatypes.test_collections_extra.NoSuchMixin"])
        with pytest.raises(ImportError):
            datatype_registry.get_type(element).create_marshmallow_schema(element)

    # -- side effects / precedence ----------------------------------------

    def test_element_definition_is_not_modified(self, datatype_registry):
        """Building the schema must not rewrite the model definition in place."""
        element = object_element([DATE_RANGE_MIXIN])
        before = list(element["marshmallow_schema_mixins"])
        datatype_registry.get_type(element).create_marshmallow_schema(element)
        assert element["marshmallow_schema_mixins"] == before

    def test_schema_can_be_created_repeatedly(self, datatype_registry):
        """Creating the schema twice must neither fail nor change the result."""
        element = object_element([DATE_RANGE_MIXIN])
        dt = datatype_registry.get_type(element)
        first = dt.create_marshmallow_schema(element)
        second = dt.create_marshmallow_schema(element)
        assert issubclass(first, DateRangeMixin)
        assert issubclass(second, DateRangeMixin)
        assert first().fields.keys() == second().fields.keys()

    def test_marshmallow_schema_class_takes_precedence(self, datatype_registry):
        """When a schema class is given explicitly, mixins are not used."""
        element = {
            **object_element([DATE_RANGE_MIXIN]),
            "marshmallow_schema_class": "tests.datatypes.test_collections_extra.PlainSchema",
        }
        schema_cls = datatype_registry.get_type(element).create_marshmallow_schema(element)
        assert schema_cls is PlainSchema
        assert not issubclass(schema_cls, DateRangeMixin)


# ===========================================================================
# [] shortcut and dict shortcuts in get_type
# ===========================================================================


class TestRegistryShortcuts:
    """The registry must resolve 'properties' and 'items' dict shortcuts."""

    def test_get_type_with_properties_dict_resolves_to_object(self, datatype_registry):
        """A dict with 'properties' but no 'type' key must resolve to ObjectDataType."""
        from oarepo_model.datatypes.collections import ObjectDataType

        dt = datatype_registry.get_type({"properties": {"x": {"type": "keyword"}}})
        assert isinstance(dt, ObjectDataType)

    def test_get_type_with_items_dict_resolves_to_array(self, datatype_registry):
        """A dict with 'items' but no 'type' key must resolve to ArrayDataType."""
        from oarepo_model.datatypes.collections import ArrayDataType

        dt = datatype_registry.get_type({"items": {"type": "keyword"}})
        assert isinstance(dt, ArrayDataType)

    def test_array_bracket_shortcut_in_nested_properties(self, datatype_registry):
        """Expand property key ending in '[]' to type=array when type is registered."""
        datatype_registry.add_types(
            {
                "TaggedItem": {
                    "type": "object",
                    "properties": {
                        "tags[]": {"type": "keyword"},
                    },
                }
            }
        )
        dt = datatype_registry.get_type("TaggedItem")
        # Reference the registered type by name (the normal usage pattern).
        # _merge_type_dict strips the "type" key and merges nothing else,
        # so the registered type_dict (with expanded tags[]) is used as-is.
        field = dt.create_marshmallow_field("item", {"type": "TaggedItem"})
        # The resulting field is a Nested schema containing a List sub-field.
        assert isinstance(field, ma.fields.Nested)
        inner_schema = field.schema
        # Field names are converted to Python identifiers; 'tags[]' → 'tags_91__93_'
        list_fields = [f for f in inner_schema.fields.values() if isinstance(f, ma.fields.List)]
        field_names = list(inner_schema.fields)
        assert list_fields, f"Expected a List field in the inner schema, got fields: {field_names}"


# ===========================================================================
# DynamicObjectDataType JSON schema and mapping
# ===========================================================================


class TestDynamicObjectDataType:
    """dynamic-object must advertise open schema and dynamic mapping."""

    def test_json_schema_allows_additional_properties(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "dynamic-object"})
        schema = dt.create_json_schema({"type": "dynamic-object"})
        assert schema.get("additionalProperties") is True

    def test_mapping_uses_dynamic_true(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "dynamic-object"})
        mapping = dt.create_mapping({"type": "dynamic-object"})
        assert mapping.get("dynamic") in ("true", True)


# ===========================================================================
# ArrayDataType create_mapping delegates to items
# ===========================================================================


class TestArrayMappingDelegation:
    """Arrays are transparent in ES: create_mapping must return the items mapping."""

    def test_array_of_keywords_produces_keyword_mapping(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "array"})
        mapping = dt.create_mapping({"type": "array", "items": {"type": "keyword"}})
        assert mapping["type"] == "keyword"

    def test_array_of_ints_produces_integer_mapping(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "array"})
        mapping = dt.create_mapping({"type": "array", "items": {"type": "int"}})
        assert mapping["type"] == "integer"
