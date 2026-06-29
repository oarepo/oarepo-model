#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for the dynamic-object bug fix.

Bug 2 — dynamic-object: arbitrary data loaded correctly but dump always returned {}
    because PermissiveSchema has no declared fields (collections.py).
"""
from __future__ import annotations

import pytest
import marshmallow as ma


def make_schema(datatype_registry, element):
    """Build a one-field marshmallow Schema for the given element dict."""
    field = datatype_registry.get_type(element).create_marshmallow_field(
        field_name="a",
        element=element,
    )
    return ma.Schema.from_dict({"a": field})()


class TestDynamicObjectRoundTrip:
    """Storing arbitrary data in a dynamic-object field and reading it back
    must produce the original value unchanged.  Before the fix, dump() always
    returned {} because PermissiveSchema declared no fields.
    """

    @pytest.fixture
    def dynamic_field(self, datatype_registry):
        element = {"type": "dynamic-object"}
        return datatype_registry.get_type(element).create_marshmallow_field(
            field_name="a", element=element
        )

    def test_field_is_raw(self, dynamic_field):
        """The marshmallow field for dynamic-object must be fields.Raw, not Nested,
        so that both load and dump pass data through without transformation.
        """
        assert isinstance(dynamic_field, ma.fields.Raw), (
            f"Expected fields.Raw, got {type(dynamic_field).__name__}"
        )

    def test_load_flat_data(self, dynamic_field):
        """Arbitrary flat key-value pairs must be accepted on load."""
        data = {"x": 1, "y": "hello", "z": True}
        result = dynamic_field.deserialize(data, "a", {})
        assert result == data

    def test_dump_flat_data(self, dynamic_field):
        """dump() must return the stored data unchanged — not {}."""
        data = {"x": 1, "y": "hello", "z": True}
        result = dynamic_field._serialize(data, "a", {})
        assert result == data, (
            f"dump() returned {result!r} instead of {data!r}; "
            "this was the bug: PermissiveSchema.dump() always returned {{}}"
        )

    def test_load_nested_data(self, dynamic_field):
        """Nested dicts and lists must survive load."""
        data = {"outer": {"inner": [1, 2, 3]}, "flag": False}
        result = dynamic_field.deserialize(data, "a", {})
        assert result == data

    def test_dump_nested_data(self, dynamic_field):
        """Nested dicts and lists must survive dump."""
        data = {"outer": {"inner": [1, 2, 3]}, "flag": False}
        result = dynamic_field._serialize(data, "a", {})
        assert result == data

    def test_full_schema_round_trip(self, datatype_registry):
        """End-to-end: load then dump through a Schema must be lossless."""
        schema = make_schema(datatype_registry, {"type": "dynamic-object"})
        original = {"a": {"nested": {"deep": "value"}, "count": 42, "tags": ["a", "b"]}}
        loaded = schema.load(original)
        dumped = schema.dump(loaded)
        assert dumped == original, (
            f"Round-trip failed: got {dumped!r}, expected {original!r}"
        )

    def test_full_schema_round_trip_with_varied_types(self, datatype_registry):
        """Round-trip must work for all JSON-serialisable value types."""
        schema = make_schema(datatype_registry, {"type": "dynamic-object"})
        original = {
            "a": {
                "string_field": "text",
                "int_field": 7,
                "float_field": 3.14,
                "bool_field": False,
                "null_field": None,
                "list_field": [1, "two", {"three": 3}],
                "nested_obj": {"deeply": {"nested": True}},
            }
        }
        assert schema.dump(schema.load(original)) == original
