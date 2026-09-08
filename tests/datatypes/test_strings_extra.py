#
# Copyright (c) 2026 University of West Bohemia
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Additional tests for string data types.

Covers:
- enum validation on keyword / fulltext / fulltext+keyword
- pattern validation
- required + implicit min_length=1 behaviour
- field options: dump_only, load_only, allow_none
- marshmallow_validate option: string form, tuple form with/without args and kwargs
- facet generation: fulltext → no facet; keyword → facet; fulltext+keyword → .keyword suffix
- mapping types for all three string types
- JSON schema type for all three string types
"""

from __future__ import annotations

import marshmallow as ma
import marshmallow.validate
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_field(datatype_registry, element):
    return datatype_registry.get_type(element).create_marshmallow_field(field_name="a", element=element)


def make_schema(datatype_registry, element):
    return ma.Schema.from_dict({"a": make_field(datatype_registry, element)})()


# ---------------------------------------------------------------------------
# Custom validator for the string form of marshmallow_validate.
# It is referenced by its fully qualified name, so it must stay at module level.
# ---------------------------------------------------------------------------

NO_SPACES_VALIDATOR = "tests.datatypes.test_strings_extra.no_spaces_validator"


def no_spaces_validator(value):
    """Reject values containing whitespace."""
    if any(character.isspace() for character in value):
        raise ma.ValidationError("whitespace is not allowed")


# ===========================================================================
# Enum validation
# ===========================================================================


class TestEnumValidation:
    """enum constraint must limit accepted values for string types."""

    @pytest.mark.parametrize("type_name", ["keyword", "fulltext", "fulltext+keyword"])
    def test_enum_accepts_valid_value(self, datatype_registry, type_name):
        schema = make_schema(
            datatype_registry,
            {"type": type_name, "enum": ["alpha", "beta", "gamma"]},
        )
        assert schema.load({"a": "alpha"}) == {"a": "alpha"}

    @pytest.mark.parametrize("type_name", ["keyword", "fulltext", "fulltext+keyword"])
    def test_enum_rejects_invalid_value(self, datatype_registry, type_name):
        schema = make_schema(
            datatype_registry,
            {"type": type_name, "enum": ["alpha", "beta", "gamma"]},
        )
        with pytest.raises(ma.ValidationError):
            schema.load({"a": "delta"})

    def test_enum_all_values_accepted(self, datatype_registry):
        """Every value in the enum list must be accepted."""
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "enum": ["x", "y", "z"]},
        )
        for val in ["x", "y", "z"]:
            assert schema.load({"a": val}) == {"a": val}


# ===========================================================================
# Pattern validation
# ===========================================================================


class TestPatternValidation:
    """pattern constraint must limit accepted values for string types."""

    def test_pattern_accepts_matching_value(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "pattern": r"^\d{4}$"},
        )
        assert schema.load({"a": "2025"}) == {"a": "2025"}

    def test_pattern_rejects_non_matching_value(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "pattern": r"^\d{4}$"},
        )
        with pytest.raises(ma.ValidationError):
            schema.load({"a": "not-four-digits"})

    def test_pattern_and_enum_can_coexist(self, datatype_registry):
        """Enum and pattern validators are both applied."""
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "enum": ["abc", "def"], "pattern": r"^[a-z]+$"},
        )
        assert schema.load({"a": "abc"}) == {"a": "abc"}
        with pytest.raises(ma.ValidationError):
            # passes pattern but not enum
            schema.load({"a": "xyz"})


# ===========================================================================
# required + implicit min_length
# ===========================================================================


class TestRequiredImpliesMinLength:
    """When required=True and no explicit min_length, the field must reject
    the empty string — because a min_length=1 validator is injected.
    """

    def test_required_rejects_empty_string(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "required": True},
        )
        with pytest.raises(ma.ValidationError):
            schema.load({"a": ""})

    def test_required_accepts_non_empty_string(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "required": True},
        )
        assert schema.load({"a": "ok"}) == {"a": "ok"}

    def test_explicit_min_length_zero_with_required_allows_empty(self, datatype_registry):
        """If min_length is explicitly set, required does NOT add its own min_length=1."""
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "required": True, "min_length": 0},
        )
        # min_length=0 means empty string is valid
        assert schema.load({"a": ""}) == {"a": ""}

    def test_max_length_alone_does_not_imply_required(self, datatype_registry):
        """max_length without required must allow empty strings."""
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "max_length": 10},
        )
        assert schema.load({"a": ""}) == {"a": ""}


# ===========================================================================
# Field options: dump_only / load_only / allow_none
# ===========================================================================


class TestFieldOptions:
    """dump_only, load_only, and allow_none must be forwarded to the marshmallow field."""

    def test_dump_only_field_is_ignored_on_load(self, datatype_registry):
        field = datatype_registry.get_type({"type": "keyword", "dump_only": True}).create_marshmallow_field(
            field_name="a", element={"type": "keyword", "dump_only": True}
        )
        assert field.dump_only is True

    def test_load_only_field_is_ignored_on_dump(self, datatype_registry):
        field = datatype_registry.get_type({"type": "keyword", "load_only": True}).create_marshmallow_field(
            field_name="a", element={"type": "keyword", "load_only": True}
        )
        assert field.load_only is True

    def test_allow_none_field_accepts_null(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "allow_none": True},
        )
        assert schema.load({"a": None}) == {"a": None}

    def test_disallow_none_by_default(self, datatype_registry):
        schema = make_schema(datatype_registry, {"type": "keyword"})
        with pytest.raises(ma.ValidationError):
            schema.load({"a": None})


# ===========================================================================
# marshmallow_validate option
# ===========================================================================


class TestMarshmallowValidateOption:
    """``marshmallow_validate`` must attach the declared validators to the field.

    The option is an array of either:
    - a string with the fully qualified name of a validator callable, or
    - a tuple ``(fully qualified name, args, kwargs)`` where ``args`` and ``kwargs``
      are optional and are used to instantiate the callable.
    """

    # -- string form -------------------------------------------------------

    @pytest.mark.parametrize("type_name", ["keyword", "fulltext", "fulltext+keyword"])
    def test_string_form_rejects_value(self, datatype_registry, type_name):
        """The imported callable rejects values for all string types."""
        schema = make_schema(
            datatype_registry,
            {"type": type_name, "marshmallow_validate": [NO_SPACES_VALIDATOR]},
        )
        with pytest.raises(ma.ValidationError):
            schema.load({"a": "two words"})

    @pytest.mark.parametrize("type_name", ["keyword", "fulltext", "fulltext+keyword"])
    def test_string_form_accepts_value(self, datatype_registry, type_name):
        """The imported callable accepts values for all string types."""
        schema = make_schema(
            datatype_registry,
            {"type": type_name, "marshmallow_validate": [NO_SPACES_VALIDATOR]},
        )
        assert schema.load({"a": "one-word"}) == {"a": "one-word"}

    def test_string_form_uses_the_callable_itself(self, datatype_registry):
        """A bare string must not be instantiated, the imported callable is used as-is."""
        field = make_field(
            datatype_registry,
            {"type": "keyword", "marshmallow_validate": [NO_SPACES_VALIDATOR]},
        )
        assert no_spaces_validator in field.validators

    # -- tuple form --------------------------------------------------------

    def test_tuple_without_arguments(self, datatype_registry):
        """Only the callable is given, so it is instantiated without arguments."""
        element = {
            "type": "keyword",
            "marshmallow_validate": [("marshmallow.validate.Length",)],
        }
        field = make_field(datatype_registry, element)
        assert any(
            isinstance(v, marshmallow.validate.Length) and v.min is None and v.max is None for v in field.validators
        )
        # an unconstrained Length validator must not reject anything
        schema = make_schema(datatype_registry, element)
        assert schema.load({"a": ""}) == {"a": ""}
        assert schema.load({"a": "a rather long value"}) == {"a": "a rather long value"}

    def test_tuple_with_positional_arguments(self, datatype_registry):
        """Positional arguments are passed to the validator constructor."""
        schema = make_schema(
            datatype_registry,
            {
                "type": "keyword",
                "marshmallow_validate": [("marshmallow.validate.Length", [3, 5])],
            },
        )
        assert schema.load({"a": "abcd"}) == {"a": "abcd"}
        with pytest.raises(ma.ValidationError):
            schema.load({"a": "ab"})
        with pytest.raises(ma.ValidationError):
            schema.load({"a": "abcdef"})

    def test_tuple_with_positional_arguments_given_as_tuple(self, datatype_registry):
        """Python models may declare the arguments as a tuple instead of a list."""
        schema = make_schema(
            datatype_registry,
            {
                "type": "keyword",
                "marshmallow_validate": [("marshmallow.validate.Length", (3, 5))],
            },
        )
        assert schema.load({"a": "abcd"}) == {"a": "abcd"}
        with pytest.raises(ma.ValidationError):
            schema.load({"a": "ab"})

    def test_tuple_with_keyword_arguments(self, datatype_registry):
        """Keyword arguments are passed to the validator constructor."""
        schema = make_schema(
            datatype_registry,
            {
                "type": "keyword",
                "marshmallow_validate": [
                    ("marshmallow.validate.Length", [], {"min": 3}),
                ],
            },
        )
        assert schema.load({"a": "abc"}) == {"a": "abc"}
        with pytest.raises(ma.ValidationError):
            schema.load({"a": "ab"})

    def test_tuple_with_positional_and_keyword_arguments(self, datatype_registry):
        """Both arguments and keyword arguments can be used together."""
        schema = make_schema(
            datatype_registry,
            {
                "type": "keyword",
                "marshmallow_validate": [
                    ("marshmallow.validate.Length", [2], {"error": "too short"}),
                ],
            },
        )
        assert schema.load({"a": "ab"}) == {"a": "ab"}
        with pytest.raises(ma.ValidationError) as exc_info:
            schema.load({"a": "a"})
        assert exc_info.value.messages["a"] == ["too short"]

    # -- several validators / interaction with the built-in ones -----------

    def test_all_declared_validators_are_applied(self, datatype_registry):
        """Every validator declared in the array is applied on load."""
        schema = make_schema(
            datatype_registry,
            {
                "type": "keyword",
                "marshmallow_validate": [
                    NO_SPACES_VALIDATOR,
                    ("marshmallow.validate.Length", [3, 5]),
                ],
            },
        )
        assert schema.load({"a": "abcd"}) == {"a": "abcd"}
        with pytest.raises(ma.ValidationError):
            # fails Length, passes the whitespace validator
            schema.load({"a": "ab"})
        with pytest.raises(ma.ValidationError):
            # passes Length, fails the whitespace validator
            schema.load({"a": "abcd efgh"})

    def test_composes_with_built_in_validators(self, datatype_registry):
        """marshmallow_validate must not replace validators built from enum/min_length."""
        element = {
            "type": "keyword",
            "min_length": 2,
            "enum": ["abcd"],
            "marshmallow_validate": [NO_SPACES_VALIDATOR],
        }
        schema = make_schema(datatype_registry, element)
        assert schema.load({"a": "abcd"}) == {"a": "abcd"}
        with pytest.raises(ma.ValidationError):
            # fails the enum validator
            schema.load({"a": "wxyz"})
        with pytest.raises(ma.ValidationError):
            # fails the min_length validator
            schema.load({"a": "a"})
        with pytest.raises(ma.ValidationError):
            # fails the marshmallow_validate validator
            schema.load({"a": "ab cd"})

    # -- absence of the option / invalid declarations ----------------------

    def test_no_validators_without_the_option(self, datatype_registry):
        """Without the option the field keeps the default (empty) validator list."""
        field = make_field(datatype_registry, {"type": "keyword"})
        assert field.validators == []

    def test_unknown_validator_import_path_fails(self, datatype_registry):
        """A typo in the fully qualified name must fail loudly."""
        element = {
            "type": "keyword",
            "marshmallow_validate": ["does.not.Exist"],
        }
        with pytest.raises(ImportError):
            make_field(datatype_registry, element)


# ===========================================================================
# Facet generation
# ===========================================================================


class TestStringFacets:
    """Facet behaviour differs across string types."""

    def test_fulltext_produces_no_facet(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "fulltext"})
        facets = {}
        result = dt.get_facet("metadata.title", {"type": "fulltext"}, [], facets)
        assert "metadata.title" not in result, (
            "fulltext must not produce a facet (full-text fields are not aggregatable)"
        )

    def test_keyword_produces_facet(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "keyword"})
        facets = {}
        result = dt.get_facet("metadata.status", {"type": "keyword"}, [], facets)
        assert "metadata.status" in result, "keyword must produce a facet"

    def test_fulltext_keyword_facet_uses_keyword_suffix(self, datatype_registry):
        """The facet entry for fulltext+keyword must reference the .keyword sub-field
        in its field descriptor, even though the facet dict key keeps the original path.
        """
        dt = datatype_registry.get_type({"type": "fulltext+keyword"})
        facets = {}
        result = dt.get_facet("metadata.title", {"type": "fulltext+keyword"}, [], facets)
        assert "metadata.title" in result
        # The TermsFacet 'field' value must point to the .keyword sub-field
        facet_def = result["metadata.title"]
        field_values = [entry.get("field", "") for entry in (facet_def if isinstance(facet_def, list) else [facet_def])]
        assert any(".keyword" in f for f in field_values), f"Expected .keyword in facet field, got: {field_values}"

    def test_fulltext_keyword_facet_path_structure(self, datatype_registry):
        """The facet field for fulltext+keyword must be 'original_path.keyword'."""
        dt = datatype_registry.get_type({"type": "fulltext+keyword"})
        facets = {}
        result = dt.get_facet("metadata.title", {"type": "fulltext+keyword"}, [], facets)
        assert "metadata.title" in result
        facet_def = result["metadata.title"]
        entries = facet_def if isinstance(facet_def, list) else [facet_def]
        fields = [e.get("field", "") for e in entries]
        assert "metadata.title.keyword" in fields


# ===========================================================================
# Mapping types
# ===========================================================================


class TestStringMappings:
    """Each string type must produce its correct Elasticsearch mapping."""

    def test_keyword_mapping_type(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "keyword"})
        mapping = dt.create_mapping({"type": "keyword"})
        assert mapping["type"] == "keyword"

    def test_fulltext_mapping_type(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "fulltext"})
        mapping = dt.create_mapping({"type": "fulltext"})
        assert mapping["type"] == "text"

    def test_fulltext_keyword_mapping_has_keyword_subfield(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "fulltext+keyword"})
        mapping = dt.create_mapping({"type": "fulltext+keyword"})
        assert mapping["type"] == "text"
        assert mapping["fields"]["keyword"]["type"] == "keyword"

    def test_keyword_json_schema_type_is_string(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "keyword"})
        schema = dt.create_json_schema({"type": "keyword"})
        assert schema["type"] == "string"

    def test_fulltext_json_schema_type_is_string(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "fulltext"})
        schema = dt.create_json_schema({"type": "fulltext"})
        assert schema["type"] == "string"
