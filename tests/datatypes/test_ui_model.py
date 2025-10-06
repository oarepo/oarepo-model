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
        "help": {"und": ""},
        "label": {"und": "a"},
        "hint": {"und": ""},
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
        "help": {"und": ""},
        "label": {"und": "a"},
        "hint": {"und": ""},
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
        "help": {"und": ""},
        "label": {"und": "a"},
        "hint": {"und": ""},
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
        "help": {"und": ""},
        "label": {"und": "a"},
        "hint": {"und": ""},
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
        "help": {"und": ""},
        "label": {"und": "a"},
        "hint": {"und": ""},
        "min_inclusive": 0.0,
        "max_inclusive": 100.0,
    }


def test_boolean_ui_model(test_ui_model):
    ui_model = test_ui_model({"type": "boolean"})
    assert ui_model == {
        "input": "boolean",
        "help": {"und": ""},
        "label": {"und": "a"},
        "hint": {"und": ""},
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
        "help": {"und": ""},
        "label": {"und": "a"},
        "hint": {"und": ""},
        "children": {
            "name": {
                "input": "keyword",
                "help": {"und": ""},
                "label": {"und": "name"},
                "hint": {"und": ""},
                "required": True,
            },
            "age": {
                "input": "int",
                "help": {"und": ""},
                "label": {"und": "age"},
                "hint": {"und": ""},
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
        "help": {"und": ""},
        "label": {"und": "a"},
        "hint": {"und": ""},
        "children": {
            "person": {
                "input": "object",
                "help": {"und": ""},
                "label": {"und": "person"},
                "hint": {"und": ""},
                "required": True,
                "children": {
                    "name": {
                        "input": "keyword",
                        "help": {"und": ""},
                        "label": {"und": "name"},
                        "hint": {"und": ""},
                        "required": True,
                    },
                    "age": {
                        "input": "int",
                        "help": {"und": ""},
                        "label": {"und": "age"},
                        "hint": {"und": ""},
                        "min_inclusive": 0,
                    },
                },
            },
        },
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
        "help": {"und": ""},
        "label": {"und": "a"},
        "hint": {"und": ""},
        "child": {
            "input": "keyword",
            "help": {"und": ""},
            "label": {"und": "item"},
            "hint": {"und": ""},
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
        "help": {"und": ""},
        "label": {"und": "a"},
        "hint": {"und": ""},
        "min_items": 1,
        "max_items": 3,
        "child": {
            "input": "object",
            "help": {"und": ""},
            "label": {"und": "item"},
            "hint": {"und": ""},
            "children": {
                "name": {
                    "input": "keyword",
                    "help": {"und": ""},
                    "label": {"und": "name"},
                    "hint": {"und": ""},
                    "required": True,
                },
                "age": {
                    "input": "int",
                    "help": {"und": ""},
                    "label": {"und": "age"},
                    "hint": {"und": ""},
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
        "help": {"und": ""},
        "label": {"und": "a"},
        "hint": {"und": ""},
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
        "help": {"und": ""},
        "label": {"und": "a"},
        "hint": {"und": ""},
        "children": {
            "name": {
                "input": "keyword",
                "help": {"und": ""},
                "label": {"und": "name"},
                "hint": {"und": ""},
                "required": True,
            },
            "age": {
                "input": "int",
                "help": {"und": ""},
                "label": {"und": "age"},
                "hint": {"und": ""},
                "min_inclusive": 0,
            },
        },
    }


def test_multilingual_labels_hints_help(test_ui_model):
    """Ensure multilingual label, hint, and help texts are preserved in UI models."""
    ui_model = test_ui_model(
        {
            "type": "object",
            "label": {"cs": "Osoba", "en": "Person"},
            "hint": {"cs": "Vyplňte údaje o osobě", "en": "Fill in person details"},
            "help": {"cs": "Pomoc s formulářem", "en": "Form assistance"},
            "properties": {
                "name": {
                    "type": "keyword",
                    "label": {"cs": "Jméno", "en": "Name"},
                    "hint": {"cs": "Zadejte celé jméno", "en": "Enter full name"},
                    "help": {"cs": "Musí být kratší než 50 znaků", "en": "Must be shorter than 50 chars"},
                },
                "addresses": {
                    "type": "array",
                    "label": {"cs": "Adresy", "en": "Addresses"},
                    "hint": {"cs": "Můžete zadat více adres", "en": "You can enter multiple addresses"},
                    "help": {"cs": "Klikněte na + pro přidání nové", "en": "Click + to add another"},
                    "items": {
                        "type": "object",
                        "label": {"cs": "Adresa", "en": "Address"},
                        "properties": {
                            "street": {
                                "type": "keyword",
                                "label": {"cs": "Ulice", "en": "Street"},
                                "hint": {"cs": "Zadejte název ulice", "en": "Enter street name"},
                            },
                            "city": {
                                "type": "keyword",
                                "label": {"cs": "Město", "en": "City"},
                                "help": {"cs": "Vyberte ze seznamu", "en": "Choose from list"},
                            },
                        },
                    },
                },
            },
        },
    )

    assert ui_model["label"] == {"cs": "Osoba", "en": "Person"}
    assert ui_model["hint"] == {"cs": "Vyplňte údaje o osobě", "en": "Fill in person details"}
    assert ui_model["help"] == {"cs": "Pomoc s formulářem", "en": "Form assistance"}

    name_field = ui_model["children"]["name"]
    assert name_field["label"] == {"cs": "Jméno", "en": "Name"}
    assert name_field["hint"]["cs"].startswith("Zadejte celé jméno")
    assert name_field["help"]["en"].endswith("Must be shorter than 50 chars")

    addresses_field = ui_model["children"]["addresses"]
    assert addresses_field["label"]["en"] == "Addresses"
    assert addresses_field["hint"]["cs"] == "Můžete zadat více adres"
    assert addresses_field["help"]["en"].startswith("Click")

    child = addresses_field["child"]
    assert child["label"] == {"cs": "Adresa", "en": "Address"}
    assert set(child["children"].keys()) == {"street", "city"}

    street = child["children"]["street"]
    assert street["label"]["cs"] == "Ulice"
    assert "Zadejte" in street["hint"]["cs"]

    city = child["children"]["city"]
    assert city["label"]["en"] == "City"
    assert "Vyberte" in city["help"]["cs"]
