#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for the polymorphic bug fix.

Bug 3 — polymorphic: ValidationError "Unknown field" on store because the discriminator
    key was passed to the sub-schema which had unknown=RAISE; discriminator was also
    silently dropped on dump; unrecognised discriminator raised AssertionError instead
    of ValidationError (polymorphic.py).
"""
from __future__ import annotations

import pytest
import marshmallow as ma


def make_schema(datatype_registry, element, extra_types=None):
    """Build a one-field marshmallow Schema for the given element dict."""
    if extra_types:
        datatype_registry.add_types(extra_types)
    field = datatype_registry.get_type(element).create_marshmallow_field(
        field_name="a",
        element=element,
    )
    return ma.Schema.from_dict({"a": field})()


# Sub-schemas used across polymorphic tests.
# NOTE: the discriminator key ("kind") is intentionally NOT declared as a
# property of either sub-schema — that is precisely what triggered the bug.
_TYPE_A_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "fulltext+keyword", "required": True},
        "is_cheese": {"type": "boolean"},
    },
}
_TYPE_B_SCHEMA = {
    "type": "object",
    "properties": {
        "count": {"type": "int"},
    },
}
_POLYMORPHIC_ELEMENT = {
    "type": "polymorphic",
    "discriminator": "kind",
    "oneof": [
        {"discriminator": "type_a", "type": "TypeA"},
        {"discriminator": "type_b", "type": "TypeB"},
    ],
}
_EXTRA_TYPES = {"TypeA": _TYPE_A_SCHEMA, "TypeB": _TYPE_B_SCHEMA}


class TestPolymorphicDiscriminatorHandling:
    """PolymorphicField must strip the discriminator before passing the value
    to the sub-schema on load, re-add it on dump, and raise a proper
    ValidationError for unknown discriminator values.
    """

    @pytest.fixture
    def schema(self, datatype_registry):
        return make_schema(datatype_registry, _POLYMORPHIC_ELEMENT, _EXTRA_TYPES)

    # --- deserialization (load) ---

    def test_load_does_not_raise_unknown_field_for_discriminator(self, schema):
        """Loading a value that includes the discriminator key must not raise
        ValidationError 'Unknown field' — the discriminator must be stripped
        before the sub-schema validates the payload.
        """
        # Before the fix this raised: ValidationError: {'kind': ['Unknown field.']}
        result = schema.load({"a": {"kind": "type_a", "name": "Muenster", "is_cheese": True}})
        assert result is not None

    def test_load_preserves_discriminator_in_result(self, schema):
        """The deserialized dict must contain the discriminator key so that
        subsequent serialization can reconstruct the full document.
        """
        result = schema.load({"a": {"kind": "type_a", "name": "Muenster", "is_cheese": True}})
        assert result["a"]["kind"] == "type_a", (
            "Discriminator must be put back into the deserialized result"
        )

    def test_load_validates_sub_schema_fields(self, schema):
        """The sub-schema validation must still run: fields with wrong types
        must be rejected even after the discriminator stripping fix.
        """
        with pytest.raises(ma.ValidationError):
            # 'name' is required for type_a
            schema.load({"a": {"kind": "type_a", "is_cheese": True}})

    def test_load_rejects_unknown_fields_in_sub_schema(self, schema):
        """Extra fields that are not declared in the sub-schema must still
        be rejected (unknown=RAISE is preserved for payload fields).
        """
        with pytest.raises(ma.ValidationError):
            schema.load({"a": {"kind": "type_a", "name": "ok", "surprise": "boom"}})

    def test_load_second_variant(self, schema):
        """The fix must work for every discriminator variant, not just the first."""
        result = schema.load({"a": {"kind": "type_b", "count": 5}})
        assert result["a"]["kind"] == "type_b"
        assert result["a"]["count"] == 5

    # --- serialization (dump) ---

    def test_dump_preserves_discriminator(self, schema):
        """dump() must include the discriminator key in its output.
        Before the fix it was silently dropped because the sub-schema only
        serializes declared fields.
        """
        loaded = schema.load({"a": {"kind": "type_a", "name": "Gouda", "is_cheese": True}})
        dumped = schema.dump(loaded)
        assert "kind" in dumped["a"], (
            "Discriminator key must be present in the serialized output"
        )
        assert dumped["a"]["kind"] == "type_a"

    def test_dump_preserves_payload_fields(self, schema):
        """dump() must include the sub-schema fields as well as the discriminator."""
        loaded = schema.load({"a": {"kind": "type_a", "name": "Gouda", "is_cheese": True}})
        dumped = schema.dump(loaded)
        assert dumped["a"]["name"] == "Gouda"
        assert dumped["a"]["is_cheese"] is True

    # --- full round-trip ---

    def test_full_round_trip_type_a(self, schema):
        """A complete load → dump round-trip must be lossless for type_a."""
        original = {"a": {"kind": "type_a", "name": "Brie", "is_cheese": True}}
        assert schema.dump(schema.load(original)) == original

    def test_full_round_trip_type_b(self, schema):
        """A complete load → dump round-trip must be lossless for type_b."""
        original = {"a": {"kind": "type_b", "count": 99}}
        assert schema.dump(schema.load(original)) == original

    # --- error handling ---

    def test_unknown_discriminator_raises_validation_error(self, schema):
        """An unrecognised discriminator value must raise marshmallow.ValidationError,
        not AssertionError.  Before the fix, self.fail('unknown_type', ...) raised
        AssertionError because 'unknown_type' was not in error_messages.
        """
        with pytest.raises(ma.ValidationError) as exc_info:
            schema.load({"a": {"kind": "not_a_real_type", "name": "x"}})
        # The error message must be a string, not an AssertionError traceback
        messages = exc_info.value.messages
        assert isinstance(messages, dict)

    def test_unknown_discriminator_error_message_names_valid_types(self, schema):
        """The ValidationError for an unknown discriminator must mention the
        valid types so the caller knows what values are accepted.
        """
        with pytest.raises(ma.ValidationError) as exc_info:
            schema.load({"a": {"kind": "nope", "x": 1}})
        error_text = str(exc_info.value.messages)
        assert "type_a" in error_text or "type_b" in error_text, (
            f"Error message should list valid types, got: {error_text}"
        )

    def test_missing_discriminator_raises_validation_error(self, schema):
        """A payload that lacks the discriminator key entirely must raise
        ValidationError, not KeyError or AttributeError.
        """
        with pytest.raises(ma.ValidationError):
            schema.load({"a": {"name": "no discriminator here"}})

    # --- polymorphic in array ---

    def test_polymorphic_in_array_round_trip(self, datatype_registry):
        """The same discriminator-stripping fix must apply when polymorphic
        appears as items in an array field.
        """
        schema = make_schema(
            datatype_registry,
            {
                "type": "array",
                "items": _POLYMORPHIC_ELEMENT,
            },
            _EXTRA_TYPES,
        )
        original = {
            "a": [
                {"kind": "type_a", "name": "Cheddar", "is_cheese": True},
                {"kind": "type_b", "count": 3},
            ]
        }
        assert schema.dump(schema.load(original)) == original
