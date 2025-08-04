#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.fixture
def test_ui_model(datatype_registry) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def _test_ui_model(
        element: dict[str, Any],
        extra_types: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if extra_types:
            datatype_registry.add_types(extra_types)
        return datatype_registry.get_type(element).create_ui_model(
            element=element,
            path=["a"],
        )

    return _test_ui_model


def test_keyword_ui_model(test_ui_model):
    ui_model = test_ui_model(
        {
            "type": "keyword",
            "min_length": 1,
            "max_length": 10,
            "pattern": "^[a-zA-Z ]+$",
        },
    )
    assert ui_model == {
        "input": "keyword",
        "help": "a.help",
        "label": "a.label",
        "hint": "a.hint",
        "min_length": 1,
        "max_length": 10,
        "pattern": "^[a-zA-Z ]+$",
    }


def test_fulltext_ui_model(test_ui_model):
    ui_model = test_ui_model(
        {
            "type": "fulltext",
            "min_length": 1,
            "max_length": 10,
            "pattern": "^[a-zA-Z ]+$",
        },
    )
    assert ui_model == {
        "input": "fulltext",
        "help": "a.help",
        "label": "a.label",
        "hint": "a.hint",
        "min_length": 1,
        "max_length": 10,
        "pattern": "^[a-zA-Z ]+$",
    }


def test_fulltext_plus_keyword_ui_model(test_ui_model):
    ui_model = test_ui_model(
        {
            "type": "fulltext+keyword",
            "min_length": 1,
            "max_length": 10,
            "pattern": "^[a-zA-Z ]+$",
        },
    )
    assert ui_model == {
        "input": "fulltext+keyword",
        "help": "a.help",
        "label": "a.label",
        "hint": "a.hint",
        "min_length": 1,
        "max_length": 10,
        "pattern": "^[a-zA-Z ]+$",
    }


def test_integer_ui_model(test_ui_model):
    ui_model = test_ui_model(
        {
            "type": "int",
            "min_inclusive": 0,
            "max_inclusive": 100,
        },
    )
    assert ui_model == {
        "input": "int",
        "help": "a.help",
        "label": "a.label",
        "hint": "a.hint",
        "min_inclusive": 0,
        "max_inclusive": 100,
    }


def test_float_ui_model(test_ui_model):
    ui_model = test_ui_model(
        {
            "type": "float",
            "min_inclusive": 0.0,
            "max_inclusive": 100.0,
        },
    )
    assert ui_model == {
        "input": "float",
        "help": "a.help",
        "label": "a.label",
        "hint": "a.hint",
        "min_inclusive": 0.0,
        "max_inclusive": 100.0,
    }


def test_boolean_ui_model(test_ui_model):
    ui_model = test_ui_model({"type": "boolean"})
    assert ui_model == {
        "input": "boolean",
        "help": "a.help",
        "label": "a.label",
        "hint": "a.hint",
    }


def test_object_ui_model(test_ui_model):
    ui_model = test_ui_model(
        {
            "type": "object",
            "properties": {
                "name": {"type": "keyword", "required": True},
                "age": {"type": "int", "min_inclusive": 0},
            },
        },
    )
    assert ui_model == {
        "input": "object",
        "help": "a.help",
        "label": "a.label",
        "hint": "a.hint",
        "children": {
            "name": {
                "input": "keyword",
                "help": "a/name.help",
                "label": "a/name.label",
                "hint": "a/name.hint",
                "required": True,
            },
            "age": {
                "input": "int",
                "help": "a/age.help",
                "label": "a/age.label",
                "hint": "a/age.hint",
                "min_inclusive": 0,
            },
        },
    }


def test_object_inside_object_ui_model(test_ui_model):
    ui_model = test_ui_model(
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
    assert ui_model == {
        "input": "object",
        "help": "a.help",
        "label": "a.label",
        "hint": "a.hint",
        "children": {
            "person": {
                "input": "object",
                "help": "a/person.help",
                "label": "a/person.label",
                "hint": "a/person.hint",
                "required": True,
                "children": {
                    "name": {
                        "input": "keyword",
                        "help": "a/person/name.help",
                        "label": "a/person/name.label",
                        "hint": "a/person/name.hint",
                        "required": True,
                    },
                    "age": {
                        "input": "int",
                        "help": "a/person/age.help",
                        "label": "a/person/age.label",
                        "hint": "a/person/age.hint",
                        "min_inclusive": 0,
                    },
                },
            },
        },
    }

def test_i18n_schema(test_ui_model):
    ui_model = test_ui_model(
        {
            "type": "i18n",

        }
    )
    assert ui_model == {
            'help': 'a.help',
            'label': 'a.label',
            'hint': 'a.hint',
            'input': 'i18n',
            'children': {
                'lang': {
                    'help': 'a/lang.help',
                    'label': 'a/lang.label',
                    'hint': 'a/lang.hint',
                    'required': True,
                    'input': 'keyword'},
                'value': {
                    'help': 'a/value.help',
                    'label': 'a/value.label',
                    'hint': 'a/value.hint',
                    'required': True,
                    'input': 'keyword'
                }
            }
    }


def test_multilingual_schema(test_ui_model):
    ui_model = test_ui_model(
        {
            "type": "multilingual",

        }
    )
    print(ui_model)
    assert ui_model == {
        'help': 'a.help',
        'label': 'a.label',
        'hint': 'a.hint',
        'input': 'multilingual',
        'child': {
            'help': 'a/item.help',
            'label': 'a/item.label',
            'hint': 'a/item.hint',
            'input': 'object',
            'children':
                {'lang': {
                    'help': 'a/lang.help',
                    'label': 'a/lang.label',
                    'hint': 'a/lang.hint',
                    'required': True,
                    'input': 'keyword'
                }, 'value': {
                    'help': 'a/value.help',
                    'label': 'a/value.label',
                    'hint': 'a/value.hint',
                    'required': True,
                    'input': 'keyword'}
                }
        }
    }

def test_array(test_ui_model):
    ui_model = test_ui_model(
        {
            "type": "array",
            "items": {"type": "keyword"},
            "min_items": 1,
            "max_items": 5,
        },
    )
    assert ui_model == {
        "input": "array",
        "help": "a.help",
        "label": "a.label",
        "hint": "a.hint",
        "child": {
            "input": "keyword",
            "help": "a/item.help",
            "label": "a/item.label",
            "hint": "a/item.hint",
        },
        "min_items": 1,
        "max_items": 5,
    }


def test_array_of_objects(test_ui_model):
    ui_model = test_ui_model(
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
    assert ui_model == {
        "input": "array",
        "help": "a.help",
        "label": "a.label",
        "hint": "a.hint",
        "min_items": 1,
        "max_items": 3,
        "child": {
            "input": "object",
            "help": "a/item.help",
            "label": "a/item.label",
            "hint": "a/item.hint",
            "children": {
                "name": {
                    "input": "keyword",
                    "help": "a/name.help",
                    "label": "a/name.label",
                    "hint": "a/name.hint",
                    "required": True,
                },
                "age": {
                    "input": "int",
                    "help": "a/age.help",
                    "label": "a/age.label",
                    "hint": "a/age.hint",
                    "min_inclusive": 0,
                },
            },
        },
    }


def test_forwarded_ui_model(test_ui_model):
    # Test a schema that forwards to another schema
    price = {
        "type": "double",
    }
    ui_model = test_ui_model(
        {"type": "price"},
        extra_types={
            "price": price,
        },
    )
    assert ui_model == {
        "input": "double",
        "help": "a.help",
        "label": "a.label",
        "hint": "a.hint",
    }


def test_forwarded_object_ui_model(test_ui_model):
    # Test a schema that forwards to an object schema
    person = {
        "type": "object",
        "properties": {
            "name": {"type": "keyword", "required": True},
            "age": {"type": "int", "min_inclusive": 0},
        },
    }
    ui_model = test_ui_model(
        {"type": "person"},
        extra_types={
            "person": person,
        },
    )
    assert ui_model == {
        "input": "object",
        "help": "a.help",
        "label": "a.label",
        "hint": "a.hint",
        "children": {
            "name": {
                "input": "keyword",
                "help": "a/name.help",
                "label": "a/name.label",
                "hint": "a/name.hint",
                "required": True,
            },
            "age": {
                "input": "int",
                "help": "a/age.help",
                "label": "a/age.label",
                "hint": "a/age.hint",
                "min_inclusive": 0,
            },
        },
    }
