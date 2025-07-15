from typing import Any, Callable

import marshmallow as ma
import pytest


@pytest.fixture
def test_schema(datatype_registry) -> Callable[[dict[str, Any]], ma.Schema]:
    def _test_schema(
        element: dict[str, Any], extra_types: dict[str, Any] | None = None
    ) -> ma.Schema:
        if extra_types:
            datatype_registry.add_types(extra_types)
        fld = datatype_registry.get_type(element).create_marshmallow_field(
            field_name="a", element=element
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
        }
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
        }
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
        }
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
        }
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
        }
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
        }
    )
    assert schema.load({"a": {"name": "John", "age": 30}}) == {
        "a": {"name": "John", "age": 30}
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
                }
            },
        }
    )
    assert schema.load({"a": {"person": {"name": "Alice", "age": 25}}}) == {
        "a": {"person": {"name": "Alice", "age": 25}}
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
        }
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
        }
    )
    assert schema.load(
        {"a": [{"name": "Bob", "age": 30}, {"name": "Alice", "age": 25}]}
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
                ]
            }
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
        "a": {"name": "John", "age": 30}
    }
    with pytest.raises(ma.ValidationError):
        schema.load({"a": {"name": "", "age": 30}})
    with pytest.raises(ma.ValidationError):
        schema.load({"a": {"name": "John", "age": -5}})
