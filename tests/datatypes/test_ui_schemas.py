from datetime import time
from typing import Any, Callable

import marshmallow as ma
import pytest
from babel.numbers import format_decimal
from flask_babel import get_locale


@pytest.fixture
def test_ui_schema(datatype_registry) -> Callable[[dict[str, Any]], ma.Schema]:
    def _test_schema(
        element: dict[str, Any], extra_types: dict[str, Any] | None = None
    ) -> ma.Schema:
        if extra_types:
            datatype_registry.add_types(extra_types)
        flds = datatype_registry.get_type(element).create_ui_marshmallow_fields(
            field_name="a", element=element
        )
        return ma.Schema.from_dict(flds)()

    return _test_schema


def test_keyword_ui_schema(test_ui_schema):
    schema = test_ui_schema(
        {
            "type": "keyword",
        }
    )
    assert (
        schema.dump({"a": "test"}) == {}
    )  # no ui serialization -> we can leave it out


def test_date_ui_schema(test_ui_schema):
    schema = test_ui_schema(
        {
            "type": "date",
        }
    )

    assert schema.dump({"a": "2023-01-01"}) == {
        "a_l10n_medium": "Jan 1, 2023",
        "a_l10n_long": "January 1, 2023",
        "a_l10n_short": "1/1/23",
        "a_l10n_full": "Sunday, January 1, 2023",
    }


def test_datetime_ui_schema(test_ui_schema):
    schema = test_ui_schema(
        {
            "type": "datetime",
        }
    )

    assert schema.dump({"a": "2023-01-01T12:30:00"}) == {
        "a_l10n_medium": "Jan 1, 2023, 12:30:00\u202fPM",
        "a_l10n_long": "January 1, 2023, 12:30:00\u202fPM UTC",
        "a_l10n_short": "1/1/23, 12:30\u202fPM",
        "a_l10n_full": "Sunday, January 1, 2023, 12:30:00\u202fPM Coordinated Universal Time",
    }


def test_time_ui_schema(test_ui_schema):
    schema = test_ui_schema(
        {
            "type": "time",
        },
    )

    res = schema.dump({"a": time(12, 30)})
    assert res
    assert res.keys() == {"a_l10n_long", "a_l10n_medium", "a_l10n_short", "a_l10n_full"}


def test_boolean_ui_schema(test_ui_schema):
    schema = test_ui_schema(
        {
            "type": "boolean",
        }
    )

    assert schema.dump({"a": True}) == {"a_i18n": "true"}

    assert schema.dump({"a": False}) == {"a_i18n": "false"}


def test_numbers_ui_schema(test_ui_schema):
    schema = test_ui_schema(
        {
            "type": "int",
        }
    )

    loc = str(get_locale()) if get_locale() else None
    val = format_decimal(1000000, locale=loc)
    assert schema.dump({"a": 1000000}) == {"a": val}

    schema = test_ui_schema(
        {
            "type": "float",
        }
    )

    val = format_decimal(123.456, locale=loc)
    assert schema.dump({"a": 123.456}) == {"a": val}

    val = format_decimal(123456, locale=loc)
    assert schema.dump({"a": 123456}) == {"a": val}


def test_object_ui_schema(test_ui_schema):
    schema = test_ui_schema(
        {
            "type": "object",
            "properties": {
                "name": {"type": "keyword", "required": True},
                "age": {"type": "int", "min_inclusive": 0},
            },
        }
    )

    test_data = {"a": {"name": "John", "age": 30}}

    assert schema.dump(test_data) == {"a": {"age": "30"}}


def test_object_inside_object_schema(test_ui_schema):
    schema = test_ui_schema(
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
    assert schema.dump({"a": {"person": {"name": "Alice", "age": 25}}}) == {
        "a": {"person": {"age": "25"}}
    }


def test_array_ui_ints(test_ui_schema):
    schema = test_ui_schema(
        {
            "type": "array",
            "items": {"type": "int"},
            "min_items": 1,
            "max_items": 5,
        }
    )

    loc = str(get_locale()) if get_locale() else None
    val1 = format_decimal(123.456, locale=loc)
    val2 = format_decimal(10000, locale=loc)
    res = schema.dump({"a": [123.456, 10000]})
    assert res == {"a": [val1, val2]}

    res = schema.dump({"a": []})
    assert res == {"a": []}


def test_array_ui_bools(test_ui_schema):
    schema = test_ui_schema(
        {
            "type": "array",
            "items": {"type": "boolean"},
            "min_items": 1,
            "max_items": 5,
        }
    )

    res = schema.dump({"a": [True, True, False]})
    assert res == {"a": ["true", "true", "false"]}

    res = schema.dump({"a": []})
    assert res == {"a": []}


def test_array_ui_strings(test_ui_schema):
    schema = test_ui_schema(
        {
            "type": "array",
            "items": {"type": "keyword"},
            "min_items": 1,
            "max_items": 5,
        }
    )

    res = schema.dump({"a": ["keyword1", "keyword2", "keyword3"]})
    assert not res


def test_array_ui_of_objects(test_ui_schema):
    schema = test_ui_schema(
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

    res = schema.dump({"a": [{"name": "Bob", "age": 30}, {"name": "Alice", "age": 25}]})
    assert res == {
        "a": [
            {"age": "30"},
            {"age": "25"},
        ]
    }


def test_forwarded_object_ui_schema(test_ui_schema):
    person = {
        "type": "object",
        "properties": {
            "name": {"type": "keyword", "required": True},
            "age": {"type": "int", "min_inclusive": 0},
        },
    }
    schema = test_ui_schema(
        {"type": "person"},
        extra_types={
            "person": person,
        },
    )

    res = schema.dump({"a": {"name": "John", "age": 30}})
    assert res == {"a": {"age": "30"}}


def test_forwarded_object_with_array_ui_schema(test_ui_schema):
    person = {
        "type": "object",
        "properties": {
            "name": {"type": "keyword", "required": True},
            "measurements": {"type": "array", "items": {"type": "float"}},
        },
    }
    schema = test_ui_schema(
        {"type": "person"},
        extra_types={
            "person": person,
        },
    )

    res = schema.dump({"a": {"name": "John", "measurements": [123, 456, 789, 123.456]}})
    assert res == {"a": {"measurements": ["123", "456", "789", "123.456"]}}


def test_multiple_items_in_dictionary_in_array(test_ui_schema):
    person = {
        "type": "object",
        "properties": {
            "name": {"type": "keyword", "required": True},
            "measurements": {"type": "array", "items": {"type": "float"}},
        },
    }

    schema = test_ui_schema(
        {
            "type": "array",
            "items": {
                "type": "person",
            },
        },
        extra_types={
            "person": person,
        },
    )

    res = schema.dump(
        {"a": [{"name": "John", "measurements": [123, 456, 789, 123.456]}]}
    )
    assert res == {"a": [{"measurements": ["123", "456", "789", "123.456"]}]}


def test_ui_schema_multiple_transformations(test_ui_schema):
    schema = test_ui_schema(
        {
            "type": "array",
            "items": {
                "type": "date",
            },
        }
    )

    res = schema.dump({"a": ["2023-01-02"]})
    assert res
    assert len(res["a"]) == 1
    assert len(res["a"][0]) == 4
    for transformed_val in res["a"]:
        assert transformed_val.keys() == {
            "item_l10n_long",
            "item_l10n_medium",
            "item_l10n_short",
            "item_l10n_full",
        }

    res = schema.dump({"a": ["2023-01-02", "2023-12-12"]})
    assert res
    assert len(res["a"]) == 2
    assert len(res["a"][0]) == 4
    assert len(res["a"][1]) == 4
    for transformed_val in res["a"]:
        assert transformed_val.keys() == {
            "item_l10n_long",
            "item_l10n_medium",
            "item_l10n_short",
            "item_l10n_full",
        }


def test_ui_every_format_in_object(test_ui_schema):
    person = {
        "type": "object",
        "properties": {
            "name": {"type": "keyword", "required": True},
            "measurements": {"type": "array", "items": {"type": "float"}},
            "birthday": {"type": "date"},
        },
    }

    schema = test_ui_schema(
        {
            "type": "object",
            "properties": {
                "name": {"type": "keyword"},
                "age": {"type": "int"},
                "height": {"type": "float"},
                "date": {"type": "date"},
                "some_other_date": {"type": "date"},
                "is_draft": {"type": "boolean"},
                "arrays": {
                    "type": "object",
                    "properties": {
                        "array_bool": {"type": "array", "items": {"type": "boolean"}},
                        "array_strings": {
                            "type": "array",
                            "items": {"type": "keyword"},
                        },
                        "array_int": {"type": "array", "items": {"type": "int"}},
                        "array_float": {"type": "array", "items": {"type": "float"}},
                        "array_date": {"type": "array", "items": {"type": "date"}},
                    },
                },
                "array_of_objects": {"type": "array", "items": {"type": "person"}},
            },
        },
        extra_types={"person": person},
    )

    res = schema.dump(
        {
            "a": {
                "name": "John Doe",
                "age": 30,
                "height": 1.82,
                "is_draft": True,
                "date": "2023-12-31",
                "some_other_date": "2023-12-31",
                "arrays": {
                    "array_bool": [True],
                    "array_int": [1],
                    "array_float": [1.1],
                    "array_date": ["2023-01-01"],
                    "array_strings": ["blah", "blah2"],
                },
                "array_of_objects": [
                    {
                        "name": "John",
                        "measurements": [123, 456, 789, 123.456],
                        "birthday": "2023-12-31",
                    },
                    {"name": "Johny", "measurements": [], "birthday": "2023-12-30"},
                    {"name": "Johnyy", "measurements": [123], "birthday": "2023-12-29"},
                ],
            }
        }
    )

    assert (
        res
        == {
            "a": {
                # no string formatting -> name is left out
                "age": "30",  # age is formatted but same key name is kept
                "height": "1.82",  # height is formatted but same key name is kept
                "date_l10n_long": "December 31, 2023",  # 4 different formats for the specific date
                "date_l10n_medium": "Dec 31, 2023",  # new key has prefix of an original key name
                "date_l10n_short": "12/31/23",
                "date_l10n_full": "Sunday, December 31, 2023",
                "some_other_date_l10n_long": "December 31, 2023",  # 4 different formats for the another specific date
                "some_other_date_l10n_medium": "Dec 31, 2023",  # new key has prefix of an original key name
                "some_other_date_l10n_short": "12/31/23",
                "some_other_date_l10n_full": "Sunday, December 31, 2023",
                "is_draft_i18n": "true",  # boolean is formatted always with i18n suffix
                "arrays": {
                    "array_bool": [
                        "true"
                    ],  # bools in arrays are just transformed individually a placed in array
                    "array_int": [
                        "1"
                    ],  # numbers in arrays are just transformed individually a placed in array
                    "array_float": ["1.1"],
                    "array_date": [  # each date has 4 transformations, so dictionary is created for each original date
                        {
                            "item_l10n_long": "January 1, 2023",
                            "item_l10n_medium": "Jan 1, 2023",
                            "item_l10n_short": "1/1/23",
                            "item_l10n_full": "Sunday, January 1, 2023",
                        }
                    ],
                },
                "array_of_objects": [
                    {
                        # name is left out -> no ui representation
                        "measurements": [
                            "123",
                            "456",
                            "789",
                            "123.456",
                        ],  # numbers in arrays are just transformed individually a placed in array
                        "birthday_l10n_long": "December 31, 2023",  # just testing nested structures, same logic as above
                        "birthday_l10n_medium": "Dec 31, 2023",
                        "birthday_l10n_short": "12/31/23",
                        "birthday_l10n_full": "Sunday, December 31, 2023",
                    },
                    {
                        "measurements": [],  # testing empty arrays
                        "birthday_l10n_long": "December 30, 2023",
                        "birthday_l10n_medium": "Dec 30, 2023",
                        "birthday_l10n_short": "12/30/23",
                        "birthday_l10n_full": "Saturday, December 30, 2023",
                    },
                    {
                        "measurements": ["123"],
                        "birthday_l10n_long": "December 29, 2023",
                        "birthday_l10n_medium": "Dec 29, 2023",
                        "birthday_l10n_short": "12/29/23",
                        "birthday_l10n_full": "Friday, December 29, 2023",
                    },
                ],
            }
        }
    )

    # there are 4 UI representation of a date in UI, all should be there
    assert "date_l10n_long" in res["a"]
    assert "date_l10n_medium" in res["a"]
    assert "date_l10n_short" in res["a"]
    assert "date_l10n_full" in res["a"]
    # another date representation, again all 4 should be there
    assert "some_other_date_l10n_long" in res["a"]
    assert "some_other_date_l10n_medium" in res["a"]
    assert "some_other_date_l10n_short" in res["a"]
    assert "some_other_date_l10n_full" in res["a"]

    for person in res["a"]["array_of_objects"]:
        assert "birthday_l10n_long" in person
        assert "birthday_l10n_medium" in person
        assert "birthday_l10n_short" in person
        assert "birthday_l10n_full" in person

    res = schema.dump(
        {
            "a": {
                "name": "John Doe",
                "age": 30,
                "height": 1.82,
                "is_draft": True,
                "date": "2023-12-31",
                "some_other_date": "2023-12-31",
                "arrays": {
                    "array_bool": [True, False, False],
                    "array_int": [],
                    "array_float": [1.1],
                    "array_date": ["2023-01-01", "2023-01-05"],
                    "array_strings": [],
                },
                "array_of_objects": [],
            }
        }
    )
    # same logic as above, just more tests
    assert res == {
        "a": {
            "age": "30",
            "height": "1.82",
            "date_l10n_long": "December 31, 2023",
            "date_l10n_medium": "Dec 31, 2023",
            "date_l10n_short": "12/31/23",
            "date_l10n_full": "Sunday, December 31, 2023",
            "some_other_date_l10n_long": "December 31, 2023",
            "some_other_date_l10n_medium": "Dec 31, 2023",
            "some_other_date_l10n_short": "12/31/23",
            "some_other_date_l10n_full": "Sunday, December 31, 2023",
            "is_draft_i18n": "true",
            "arrays": {
                "array_bool": ["true", "false", "false"],
                "array_int": [],
                "array_float": ["1.1"],
                "array_date": [
                    {
                        "item_l10n_long": "January 1, 2023",
                        "item_l10n_medium": "Jan 1, 2023",
                        "item_l10n_short": "1/1/23",
                        "item_l10n_full": "Sunday, January 1, 2023",
                    },
                    {
                        "item_l10n_long": "January 5, 2023",
                        "item_l10n_medium": "Jan 5, 2023",
                        "item_l10n_short": "1/5/23",
                        "item_l10n_full": "Thursday, January 5, 2023",
                    },
                ],
            },
            "array_of_objects": [],
        }
    }


def test_polymorphic_ui_schema(test_ui_schema):
    person_schema = {
        "type": "object",
        "properties": {
            "first_name": {"type": "fulltext"},
            "type": {"type": "keyword"},
            "age": {"type": "int"},
            "isActive": {"type": "boolean"},
        },
    }
    organization_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "fulltext+keyword"},
            "type": {"type": "keyword"},
            "age": {"type": "int"},
            "isFree": {"type": "boolean"},
        },
    }

    schema = test_ui_schema(
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
    loc = str(get_locale()) if get_locale() else None

    val = {"a": {"type": "person", "first_name": "bob", "age": 123, "isActive": True}}
    ret = schema.dump(val)
    formatted_number = format_decimal(123, locale=loc)
    assert ret == {
        "a": {"age": formatted_number, "isActive_i18n": "true"}
    }  # strings are removed, number and boolean are transformed

    val = {"a": {"type": "organization", "name": "CVUT", "age": 100000, "isFree": True}}
    ret = schema.dump(val)
    formatted_number = format_decimal(100000, locale=loc)
    assert ret == {
        "a": {"age": formatted_number, "isFree_i18n": "true"}
    }  # strings are removed, number and boolean are transformed


def test_polymorphic_ui_schema_in_array(test_ui_schema):
    person_schema = {
        "type": "object",
        "properties": {
            "first_name": {"type": "fulltext"},
            "type": {"type": "keyword"},
            "age": {"type": "int"},
            "isActive": {"type": "boolean"},
        },
    }
    organization_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "fulltext+keyword"},
            "type": {"type": "keyword"},
            "age": {"type": "int"},
            "isFree": {"type": "boolean"},
        },
    }

    schema = test_ui_schema(
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
    loc = str(get_locale()) if get_locale() else None

    # ---------------- 1 item in array ----------------------------
    val = {"a": [{"type": "person", "first_name": "bob", "age": 123, "isActive": True}]}
    formatted_number = format_decimal(123, locale=loc)
    ret = schema.dump(val)
    assert ret == {
        "a": [{"age": formatted_number, "isActive_i18n": "true"}]
    }  # strings are removed, number and boolean are transformed
    # -------------------------------------------------------------

    # ---------------- 1 item in array ----------------------------
    val = {
        "a": [{"type": "organization", "name": "CVUT", "age": 100000, "isFree": True}]
    }
    ret = schema.dump(val)
    formatted_number = format_decimal(100000, locale=loc)
    assert ret == {
        "a": [{"age": formatted_number, "isFree_i18n": "true"}]
    }  # strings are removed, number and boolean are transformed
    # -------------------------------------------------------------

    # ---------------- multiple items in array --------------------
    val = {
        "a": [
            {"type": "person", "first_name": "bob", "age": 123, "isActive": True},
            {"type": "person", "first_name": "bob2", "age": 0, "isActive": False},
            {"type": "organization", "name": "MIT", "age": 666, "isFree": False},
            {"type": "organization", "name": "Standford", "age": 1337, "isFree": False},
        ]
    }
    formatted_number1 = format_decimal(123, locale=loc)
    formatted_number2 = format_decimal(0, locale=loc)
    formatted_number3 = format_decimal(666, locale=loc)
    formatted_number4 = format_decimal(1337, locale=loc)
    ret = schema.dump(val)
    assert ret == {
        "a": [
            {"age": formatted_number1, "isActive_i18n": "true"},
            {"age": formatted_number2, "isActive_i18n": "false"},
            {"age": formatted_number3, "isFree_i18n": "false"},
            {"age": formatted_number4, "isFree_i18n": "false"},
        ]
    }
    # -------------------------------------------------------------


def test_polymorphic_ui_schema_in_obj(test_ui_schema):
    person_schema = {
        "type": "object",
        "properties": {
            "first_name": {"type": "fulltext"},
            "type": {"type": "keyword"},
            "age": {"type": "int"},
            "isActive": {"type": "boolean"},
        },
    }
    organization_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "fulltext+keyword"},
            "type": {"type": "keyword"},
            "age": {"type": "int"},
            "isFree": {"type": "boolean"},
        },
    }

    schema = test_ui_schema(
        {
            "type": "object",
            "properties": {
                "publication_date": {"type": "date"},
                "supported_by": {
                    "type": "polymorphic",
                    "discriminator": "type",
                    "oneof": [
                        {"discriminator": "person", "type": "Person"},
                        {"discriminator": "organization", "type": "Organization"},
                    ],
                },
            },
        },
        extra_types={"Person": person_schema, "Organization": organization_schema},
    )
    loc = str(get_locale()) if get_locale() else None

    val = {
        "a": {
            "publication_date": "2023-12-31",
            "supported_by": {
                "type": "organization",
                "name": "CVUT",
                "age": 100,
                "isFree": True,
            },
        }
    }

    ret = schema.dump(val)
    formatted_number = format_decimal(100, locale=loc)
    assert ret == {
        "a": {
            "publication_date_l10n_long": "December 31, 2023",
            "publication_date_l10n_medium": "Dec 31, 2023",
            "publication_date_l10n_short": "12/31/23",
            "publication_date_l10n_full": "Sunday, December 31, 2023",
            "supported_by": {"age": formatted_number, "isFree_i18n": "true"},
        }
    }
