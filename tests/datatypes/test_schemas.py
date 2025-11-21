#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING, Any

import marshmallow as ma
import pytest

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.fixture
def test_schema(datatype_registry) -> Callable[[dict[str, Any]], ma.Schema]:
    def _test_schema(
        element: dict[str, Any],
        extra_types: dict[str, Any] | None = None,
    ) -> ma.Schema:
        if extra_types:
            datatype_registry.add_types(extra_types)
        fld = datatype_registry.get_type(element).create_marshmallow_field(
            field_name="a",
            element=element,
        )
        return ma.Schema.from_dict({"a": fld})()

    return _test_schema


def test_keyword_schema(test_schema):
    schema = test_schema(
        {
            "type": "keyword",
            "min_length": 1,
            "max_length": 10,
            "pattern": "^[a-zA-Z ]+$",
        },
    )
    assert schema.load({"a": "test"}) == {"a": "test"}
    with pytest.raises(ma.ValidationError):
        schema.load({"a": ""})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": "this is a very long string that exceeds the maximum length"})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": "123"})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": 123})


def test_fulltext_schema(test_schema):
    schema = test_schema(
        {
            "type": "fulltext",
            "min_length": 1,
            "max_length": 10,
            "pattern": "^[a-zA-Z ]+$",
        },
    )
    assert schema.load({"a": "test"}) == {"a": "test"}
    with pytest.raises(ma.ValidationError):
        schema.load({"a": ""})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": "this is a very long string that exceeds the maximum length"})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": "123"})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": 123})


def test_fulltext_plus_keyword_schema(test_schema):
    schema = test_schema(
        {
            "type": "fulltext+keyword",
            "min_length": 1,
            "max_length": 10,
            "pattern": "^[a-zA-Z ]+$",
        },
    )
    assert schema.load({"a": "test"}) == {"a": "test"}
    with pytest.raises(ma.ValidationError):
        schema.load({"a": ""})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": "this is a very long string that exceeds the maximum length"})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": "123"})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": 123})


def test_integer_schema(test_schema):
    schema = test_schema(
        {
            "type": "int",
            "min_inclusive": 0,
            "max_inclusive": 100,
        },
    )
    assert schema.load({"a": 50}) == {"a": 50}
    with pytest.raises(ma.ValidationError):
        schema.load({"a": -1})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": 101})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": "not an integer"})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": 12.3})


def test_float_schema(test_schema):
    schema = test_schema(
        {
            "type": "float",
            "min_inclusive": 0.0,
            "max_inclusive": 100.0,
        },
    )
    assert schema.load({"a": 50.5}) == {"a": 50.5}
    with pytest.raises(ma.ValidationError):
        schema.load({"a": -1.0})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": 101.0})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": "not a float"})


def test_boolean_schema(test_schema):
    schema = test_schema({"type": "boolean"})
    assert schema.load({"a": True}) == {"a": True}
    assert schema.load({"a": False}) == {"a": False}
    with pytest.raises(ma.ValidationError):
        schema.load({"a": "not a boolean"})
    assert schema.load({"a": 1}) == {"a": True}
    assert schema.load({"a": 0}) == {"a": False}


def test_object_schema(test_schema):
    schema = test_schema(
        {
            "type": "object",
            "properties": {
                "name": {"type": "keyword", "required": True},
                "age": {"type": "int", "min_inclusive": 0},
            },
        },
    )
    assert schema.load({"a": {"name": "John", "age": 30}}) == {
        "a": {"name": "John", "age": 30},
    }
    with pytest.raises(ma.ValidationError):
        schema.load({"a": {"name": "", "age": 30}})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": {"name": "John", "age": "not an integer"}})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": {"age": 30}})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": {"name": "John", "age": -5}})


def test_object_inside_object_schema(test_schema):
    schema = test_schema(
        {
            "type": "object",
            "properties": {
                "person": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "keyword", "required": True},
                        "age": {"type": "int", "min_inclusive": 0},
                    },
                    "required": True,
                },
            },
        },
    )
    assert schema.load({"a": {"person": {"name": "Alice", "age": 25}}}) == {
        "a": {"person": {"name": "Alice", "age": 25}},
    }
    with pytest.raises(ma.ValidationError):
        schema.load({"a": {"person": {"name": "", "age": 25}}})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": {"person": {"name": "Alice", "age": -1}}})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": {}})


def test_array(test_schema):
    schema = test_schema(
        {
            "type": "array",
            "items": {"type": "keyword"},
            "min_items": 1,
            "max_items": 5,
        },
    )
    assert schema.load({"a": ["item1", "item2"]}) == {"a": ["item1", "item2"]}
    with pytest.raises(ma.ValidationError):
        schema.load({"a": []})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": ["item1", "item2", "item3", "item4", "item5", "item6"]})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": ["item1", 123]})


def test_array_of_objects(test_schema):
    schema = test_schema(
        {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "keyword", "required": True},
                    "age": {"type": "int", "min_inclusive": 0},
                },
            },
            "min_items": 1,
            "max_items": 3,
        },
    )
    assert schema.load(
        {"a": [{"name": "Bob", "age": 30}, {"name": "Alice", "age": 25}]},
    ) == {"a": [{"name": "Bob", "age": 30}, {"name": "Alice", "age": 25}]}
    with pytest.raises(ma.ValidationError):
        schema.load({"a": []})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": [{"name": "", "age": 30}]})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": [{"name": "Bob", "age": -5}]})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": [{"name": "Bob"}, {"age": 30}]})
    with pytest.raises(ma.ValidationError):
        schema.load(
            {
                "a": [
                    {"name": "Bob", "age": 30},
                    {"name": "Alice", "age": 25},
                    {"name": "Charlie", "age": 20},
                    {"name": "Dave", "age": 40},
                ],
            },
        )


def test_forwarded_schema(test_schema):
    # Test a schema that forwards to another schema
    price = {
        "type": "double",
    }
    schema = test_schema(
        {"type": "price"},
        extra_types={
            "price": price,
        },
    )
    assert schema.load({"a": 19.99}) == {"a": 19.99}
    with pytest.raises(ma.ValidationError):
        schema.load({"a": "not a number"})


def test_forwarded_object_schema(test_schema):
    # Test a schema that forwards to an object schema
    person = {
        "type": "object",
        "properties": {
            "name": {"type": "keyword", "required": True},
            "age": {"type": "int", "min_inclusive": 0},
        },
    }
    schema = test_schema(
        {"type": "person"},
        extra_types={
            "person": person,
        },
    )
    assert schema.load({"a": {"name": "John", "age": 30}}) == {
        "a": {"name": "John", "age": 30},
    }
    with pytest.raises(ma.ValidationError):
        schema.load({"a": {"name": "", "age": 30}})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": {"name": "John", "age": -5}})


def test_date_field(test_schema):
    schema = test_schema(
        {"type": "date", "min_date": date(2023, 1, 1), "max_date": date(2023, 12, 31)},
    )

    assert schema.load({"a": "2023-01-02"}) == {"a": "2023-01-02"}

    with pytest.raises(ma.ValidationError):
        schema.load({"a": "01/01/2023"})  # wrong format

    with pytest.raises(ma.ValidationError):
        schema.load({"a": 1234})  # not a date

    with pytest.raises(ma.ValidationError):
        schema.load({"a": "2022-12-31"})

    with pytest.raises(ma.ValidationError):
        schema.load({"a": "2024-01-01"})


def test_datetime_field(test_schema):
    min_dt = datetime(2023, 1, 1, 0, 0, 0)  # noqa: DTZ001 no naive datetime
    max_dt = datetime(2023, 12, 31, 23, 59, 59)  # noqa: DTZ001 no naive datetime
    schema = test_schema(
        {
            "type": "datetime",
            "min_datetime": min_dt,
            "max_datetime": max_dt,
        },
    )

    assert schema.load({"a": "2023-01-01T12:30:00"}) == {
        "a": "2023-01-01T12:30:00",
    }

    assert schema.load({"a": "2023-01-01 12:30:00"}) == {
        "a": "2023-01-01 12:30:00",
    }

    with pytest.raises(ma.ValidationError):
        assert schema.load({"a": "01/12/2022 14:15:00"})  # wrong format

    with pytest.raises(ma.ValidationError):
        schema.load({"a": "2022-12-31T23:59:59"})  # out of bounds

    with pytest.raises(ma.ValidationError):
        schema.load({"a": "2024-01-01T00:00:00"})  # out of bounds


def test_time_field(test_schema):
    schema = test_schema(
        {
            "type": "time",
            "min_time": time(9, 0, 0),
            "max_time": time(17, 0, 0),
        },
    )

    assert schema.load({"a": "12:30:00"}) == {"a": "12:30:00"}

    with pytest.raises(ma.ValidationError):
        schema.load({"a": "08:59:59"})

    with pytest.raises(ma.ValidationError):
        schema.load({"a": "01.02.2023"})

    with pytest.raises(ma.ValidationError):
        schema.load({"a": "2024-01-01T00:00:00"})

    with pytest.raises(ma.ValidationError):
        schema.load({"a": "17:00:01"})


def test_edtf_time_field(test_schema):
    schema = test_schema(
        {
            "type": "edtf-time",
        },
    )

    val = "2023"
    assert schema.load({"a": val}) == {"a": val}

    val = "2023-01-01"
    assert schema.load({"a": val}) == {"a": val}

    val = "2024-01-01T00:00:00"
    assert schema.load({"a": val}) == {"a": val}

    with pytest.raises(ma.ValidationError):
        schema.load({"a": 2023})

    with pytest.raises(ma.ValidationError):
        schema.load({"a": "12:00:00Z/13:00:00Z"})


def test_edtf_field(test_schema):
    schema = test_schema(
        {
            "type": "edtf",
        },
    )

    val = "2023-01-01"
    assert schema.load({"a": val}) == {"a": val}

    val = "2023/2025"
    with pytest.raises(ma.ValidationError):
        schema.load({"a": val})

    val = "2024-01-01T00:00:00"
    with pytest.raises(ma.ValidationError):
        schema.load({"a": val})


def test_edtf_interval_field(test_schema):
    schema = test_schema(
        {
            "type": "edtf-interval",
        },
    )

    val = "1964/2008"
    assert schema.load({"a": val}) == {"a": val}

    val = "2004-06/2006-08"
    assert schema.load({"a": val}) == {"a": val}

    val = "2004-02-01/2005-02-08"
    assert schema.load({"a": val}) == {"a": val}

    val = "2004-02-01/2005"
    assert schema.load({"a": val}) == {"a": val}

    val = "2005/2006-02"
    assert schema.load({"a": val}) == {"a": val}


def test_polymorphic_field(test_schema):
    person_schema = {
        "type": "object",
        "properties": {"first_name": {"type": "fulltext"}, "type": {"type": "keyword"}},
    }
    organization_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "fulltext+keyword"},
            "type": {"type": "keyword"},
        },
    }

    schema = test_schema(
        {
            "type": "polymorphic",
            "discriminator": "type",
            "oneof": [
                {"discriminator": "person", "type": "Person"},
                {"discriminator": "organization", "type": "Organization"},
            ],
        },
        extra_types={"Person": person_schema, "Organization": organization_schema},
    )

    val = {"a": {"type": "person", "first_name": "bob"}}
    assert schema.load(val) == val

    val = {"a": {"type": "organization", "name": "org name"}}
    assert schema.load(val) == val

    val = {"a": {"type": "person", "name": "bob"}}
    with pytest.raises(ma.ValidationError):
        schema.load(val)

    val = {"a": {"type": "organization", "first_name": "org name"}}
    with pytest.raises(ma.ValidationError):
        schema.load(val)

    val = {
        "a": {"type": "organization", "name": "org name", "full_name": "full_name"},
    }
    with pytest.raises(ma.ValidationError):
        schema.load(val)


def test_polymorphic_field_required(test_schema):
    person_schema = {
        "type": "object",
        "properties": {"first_name": {"type": "fulltext"}, "type": {"type": "keyword"}},
    }
    organization_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "fulltext+keyword"},
            "type": {"type": "keyword"},
        },
    }

    schema = test_schema(
        {
            "type": "polymorphic",
            "discriminator": "type",
            "oneof": [
                {"discriminator": "person", "type": "Person"},
                {"discriminator": "organization", "type": "Organization"},
            ],
            "required": True,
        },
        extra_types={"Person": person_schema, "Organization": organization_schema},
    )
    val = {}  # missing data
    with pytest.raises(ma.ValidationError):
        assert schema.load(val) == val


def test_polymorphic_field_in_array(test_schema):
    person_schema = {
        "type": "object",
        "properties": {"first_name": {"type": "fulltext"}, "type": {"type": "keyword"}},
    }
    organization_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "fulltext+keyword"},
            "type": {"type": "keyword"},
        },
    }

    schema = test_schema(
        {
            "type": "array",
            "items": {
                "type": "polymorphic",
                "discriminator": "type",
                "oneof": [
                    {"discriminator": "person", "type": "Person"},
                    {"discriminator": "organization", "type": "Organization"},
                ],
            },
        },
        extra_types={"Person": person_schema, "Organization": organization_schema},
    )

    val = {"a": [{"type": "person", "first_name": "bob"}]}
    assert schema.load(val) == val

    val = {"a": [{"type": "organization", "name": "org name"}]}
    assert schema.load(val) == val

    val = {
        "a": [
            {"type": "person", "first_name": "bob"},
            {"type": "person", "first_name": "bob2"},
            {"type": "organization", "name": "org name"},
            {"type": "organization", "name": "org name2"},
        ],
    }
    assert schema.load(val) == val

    val = {"a": [{"type": "person", "name": "bob"}]}
    with pytest.raises(ma.ValidationError):
        schema.load(val)

    val = {"a": [{"type": "organization", "first_name": "org name"}]}
    with pytest.raises(ma.ValidationError):
        schema.load(val)

    val = {
        "a": [
            {"type": "organization", "name": "org name", "full_name": "full_name"},
        ],
    }
    with pytest.raises(ma.ValidationError):
        schema.load(val)


def test_polymorphic_field_json_schema(test_schema):
    from oarepo_model.datatypes.registry import DataTypeRegistry

    datatype_registry = DataTypeRegistry()
    datatype_registry.load_entry_points()

    person_schema = {
        "type": "object",
        "properties": {"first_name": {"type": "fulltext"}, "type": {"type": "keyword"}},
    }
    organization_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "fulltext+keyword"},
            "type": {"type": "keyword"},
        },
    }
    polymorphic_schema = {
        "type": "polymorphic",
        "discriminator": "type",
        "oneof": [
            {"discriminator": "person", "type": "Person"},
            {"discriminator": "organization", "type": "Organization"},
        ],
    }

    extra_types = {"Person": person_schema, "Organization": organization_schema}
    datatype_registry.add_types(extra_types)

    ret = datatype_registry.get_type("polymorphic").create_json_schema(
        element=polymorphic_schema,
    )

    assert ret == {
        "oneOf": [
            {
                "type": "object",
                "unevaluatedProperties": False,
                "properties": {
                    "first_name": {"type": "string"},
                    "type": {"type": "string", "const": "person"},
                },
                "required": ["type"],
            },
            {
                "type": "object",
                "unevaluatedProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string", "const": "organization"},
                },
                "required": ["type"],
            },
        ],
    }


def test_polymorphic_field_mapping(test_schema):
    from oarepo_model.datatypes.registry import DataTypeRegistry

    datatype_registry = DataTypeRegistry()
    datatype_registry.load_entry_points()

    person_schema = {
        "type": "object",
        "properties": {"first_name": {"type": "fulltext"}, "type": {"type": "keyword"}},
    }
    organization_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "fulltext+keyword"},
            "type": {"type": "keyword"},
        },
    }
    polymorphic_schema = {
        "type": "polymorphic",
        "discriminator": "type",
        "oneof": [
            {"discriminator": "person", "type": "Person"},
            {"discriminator": "organization", "type": "Organization"},
        ],
    }

    extra_types = {"Person": person_schema, "Organization": organization_schema}
    datatype_registry.add_types(extra_types)

    ret = datatype_registry.get_type("polymorphic").create_mapping(
        element=polymorphic_schema,
    )

    # 2 keys on top level -> type and properties
    assert ret.keys() == {"type", "properties"}

    # type is object
    assert ret["type"] == "object"

    # properties has all fields from polymorphic field (from person and organization)
    assert ret["properties"].keys() == {
        "type",  # discriminator
        "first_name",  # from person
        "name",  # from org
    }

    polymorphic_schema_in_array = {
        "type": "array",
        "items": {
            "type": "polymorphic",
            "discriminator": "type",
            "oneof": [
                {"discriminator": "person", "type": "Person"},
                {"discriminator": "organization", "type": "Organization"},
            ],
        },
    }
    ret = datatype_registry.get_type("array").create_mapping(
        element=polymorphic_schema_in_array,
    )
    # 2 keys on top level -> type and properties
    assert ret.keys() == {"type", "properties"}

    # type is object
    assert ret["type"] == "object"

    # properties has all fields from polymorphic field (from person and organization)
    assert ret["properties"].keys() == {
        "type",  # discriminator
        "first_name",  # from person
        "name",  # from org
    }


class CustomSchema(ma.Schema):
    """Custom schema class for testing."""


def test_custom_schema_class(test_schema):
    schema = test_schema(
        {
            "type": "object",
            "marshmallow_schema_class": CustomSchema,
            "properties": {
                "name": {"type": "keyword", "required": True},
                "age": {"type": "int", "min_inclusive": 0},
            },
        },
    )
    fld = schema.fields["a"]
    fld_schema = fld.nested
    assert fld_schema is CustomSchema
