# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest

from oarepo_model.datatypes.base import DataType

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
                    "help": {
                        "cs": "Musí být kratší než 50 znaků",
                        "en": "Must be shorter than 50 chars",
                    },
                },
                "addresses": {
                    "type": "array",
                    "label": {"cs": "Adresy", "en": "Addresses"},
                    "hint": {
                        "cs": "Můžete zadat více adres",
                        "en": "You can enter multiple addresses",
                    },
                    "help": {
                        "cs": "Klikněte na + pro přidání nové",
                        "en": "Click + to add another",
                    },
                    "items": {
                        "type": "object",
                        "label": {"cs": "Adresa", "en": "Address"},
                        "properties": {
                            "street": {
                                "type": "keyword",
                                "label": {"cs": "Ulice", "en": "Street"},
                                "hint": {
                                    "cs": "Zadejte název ulice",
                                    "en": "Enter street name",
                                },
                            },
                            "city": {
                                "type": "keyword",
                                "label": {"cs": "Město", "en": "City"},
                                "help": {
                                    "cs": "Vyberte ze seznamu",
                                    "en": "Choose from list",
                                },
                            },
                        },
                    },
                },
            },
        },
    )

    assert ui_model["label"] == {"cs": "Osoba", "en": "Person"}
    assert ui_model["hint"] == {
        "cs": "Vyplňte údaje o osobě",
        "en": "Fill in person details",
    }
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


def test_empty_path():
    assert DataType("").create_ui_model("a", None) == {}


# ===========================================================================
# Polymorphic UI model
# ===========================================================================

PERSON_VARIANT = {
    "type": "object",
    "properties": {
        "name": {"type": "keyword", "required": True, "help": {"en": "Person name"}},
        "orcid": {"type": "keyword"},
    },
}
ORGANIZATION_VARIANT = {
    "type": "object",
    "properties": {
        "name": {"type": "keyword", "help": {"en": "Organization name"}},
        "ror": {"type": "keyword"},
    },
}


def _polymorphic_element(**overrides):
    return {
        "type": "polymorphic",
        "discriminator": "kind",
        "oneof": [
            {"discriminator": "person", "type": "Person"},
            {"discriminator": "organization", "type": "Organization"},
        ],
        **overrides,
    }


_POLY_TYPES = {"Person": PERSON_VARIANT, "Organization": ORGANIZATION_VARIANT}


def test_polymorphic_ui_model_unions_disjoint_children(test_ui_model):
    """Children that only one variant declares are both present in the union."""
    ui_model = test_ui_model(_polymorphic_element(), extra_types=_POLY_TYPES)
    assert set(ui_model["children"]) == {"name", "orcid", "ror"}
    assert ui_model["input"] == "polymorphic"


def test_polymorphic_ui_model_required_is_anded_across_variants(test_ui_model):
    """'name' is required only in person - the union must not require it."""
    ui_model = test_ui_model(_polymorphic_element(), extra_types=_POLY_TYPES)
    assert "required" not in ui_model["children"]["name"]


def test_polymorphic_ui_model_conflicting_texts_take_the_first_variant(test_ui_model):
    """Variants disagree on 'name' help - the first declaring variant's text wins."""
    ui_model = test_ui_model(_polymorphic_element(), extra_types=_POLY_TYPES)
    assert ui_model["children"]["name"]["help"] == {"en": "Person name"}


def test_polymorphic_ui_model_agreeing_required_is_kept(test_ui_model):
    """A child required by every declaring variant stays required in the union."""
    types = {
        "Person": {
            "type": "object",
            "properties": {"name": {"type": "keyword", "required": True}},
        },
        "Organization": {
            "type": "object",
            "properties": {"name": {"type": "keyword", "required": True}},
        },
    }
    ui_model = test_ui_model(_polymorphic_element(), extra_types=types)
    assert ui_model["children"]["name"]["required"] is True


def test_polymorphic_ui_model_variants_keyed_by_discriminator(test_ui_model):
    """Per-variant deviations from the union are available under 'variants'.

    A variant child identical to the union carries no information and is
    dropped - the lookup contract is variants[value] first, union as fallback.
    """
    ui_model = test_ui_model(_polymorphic_element(), extra_types=_POLY_TYPES)
    assert ui_model["discriminator"] == "kind"
    assert set(ui_model["variants"]) == {"person", "organization"}
    # 'name' differs from the union in both variants (person: required,
    # organization: different help) and is kept whole in both
    assert ui_model["variants"]["person"]["children"]["name"]["required"] is True
    assert ui_model["variants"]["person"]["children"]["name"]["help"] == {"en": "Person name"}
    assert ui_model["variants"]["organization"]["children"]["name"]["help"] == {"en": "Organization name"}
    # 'orcid'/'ror' are declared by exactly one variant each, so they always
    # equal the union and are not repeated under 'variants'
    assert "orcid" not in ui_model["variants"]["person"]["children"]
    assert "ror" not in ui_model["variants"]["organization"]["children"]


def test_polymorphic_ui_model_variants_do_not_repeat_the_unchanged_union(test_ui_model):
    """Two identical variants shrink 'variants' to a fraction of the union's size.

    Guard for the ui model size fix: repeating every variant's subtree inside
    variants grew mbdb's model by hundreds of kilobytes (oarepo_ui inlines the
    ui model into every deposit page). With the diff-only 'variants', adding a
    second identical variant must not noticeably grow the ui model.
    """
    identical_variant = {
        "type": "object",
        "properties": {
            "name": {"type": "keyword", "required": True, "help": {"en": "Person name"}},
            "orcid": {"type": "keyword"},
        },
    }
    one = test_ui_model(
        {"type": "polymorphic", "discriminator": "kind", "oneof": [{"discriminator": "person", "type": "Person"}]},
        extra_types={"Person": identical_variant},
    )
    two = test_ui_model(
        {
            "type": "polymorphic",
            "discriminator": "kind",
            "oneof": [
                {"discriminator": "person", "type": "Person"},
                {"discriminator": "person2", "type": "Person2"},
            ],
        },
        extra_types={"Person": identical_variant, "Person2": identical_variant},
    )
    # the identical second variant contributes no children to 'variants' -
    # with the old full-subtree representation it would repeat the union's
    # children wholesale
    assert two["variants"]["person2"].get("children", {}) == {}
    # compare the JSON size of a one-variant model against the same model with
    # two identical variants: near-constant growth instead of +1 union copy
    growth = len(json.dumps(two)) - len(json.dumps(one))
    assert growth < len(json.dumps(one["children"]))


def test_polymorphic_ui_model_nested_polymorphic_variant_children_are_merged(test_ui_model):
    """A variant that is itself polymorphic contributes its own merged children."""
    types = {
        "Hybrid": {
            "type": "polymorphic",
            "discriminator": "subtype",
            "oneof": [
                {"discriminator": "a", "type": "SubA"},
                {"discriminator": "b", "type": "SubB"},
            ],
        },
        "SubA": {"type": "object", "properties": {"shared": {"type": "keyword"}, "only_a": {"type": "keyword"}}},
        "SubB": {"type": "object", "properties": {"shared": {"type": "keyword"}, "only_b": {"type": "int"}}},
        "Plain": {"type": "object", "properties": {"plain": {"type": "keyword"}}},
    }
    element = {
        "type": "polymorphic",
        "discriminator": "kind",
        "oneof": [
            {"discriminator": "hybrid", "type": "Hybrid"},
            {"discriminator": "plain", "type": "Plain"},
        ],
    }
    ui_model = test_ui_model(element, extra_types=types)
    # the nested polymorphic variant's own union is merged into the outer union
    assert set(ui_model["children"]) == {"shared", "only_a", "only_b", "plain"}
    # and its exact per-variant texts stay available
    assert set(ui_model["variants"]["hybrid"]["variants"]) == {"a", "b"}


def test_polymorphic_ui_model_array_child_merged_across_variants(test_ui_model):
    """An array field whose item fields differ between variants merges with the same rules.

    The item node lives under 'child' (not 'children'), so without merging it
    the first variant's items would silently win for every other variant.
    """
    types = {
        "WithArrayA": {
            "type": "object",
            "properties": {
                "items_field": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "keyword", "required": True},
                        },
                    },
                },
            },
        },
        "WithArrayB": {
            "type": "object",
            "properties": {
                "items_field": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "keyword"},
                        },
                    },
                },
            },
        },
    }
    element = {
        "type": "polymorphic",
        "discriminator": "kind",
        "oneof": [
            {"discriminator": "a", "type": "WithArrayA"},
            {"discriminator": "b", "type": "WithArrayB"},
        ],
    }
    ui_model = test_ui_model(element, extra_types=types)
    # 'required' inside the array items is ANDed across variants, same rule as
    # for 'children': it holds only if *every* declaring variant requires it
    assert "required" not in ui_model["children"]["items_field"]["child"]["children"]["code"]
    # the variant keeps its own exact item shape
    assert ui_model["variants"]["a"]["children"]["items_field"]["child"]["children"]["code"]["required"] is True


def test_polymorphic_ui_model_oneof_item_without_discriminator_or_type_is_skipped(test_ui_model):
    """Malformed oneof entries are skipped, same as in create_mapping/create_json_schema."""
    element = _polymorphic_element()
    element["oneof"] = [{"no_discriminator": True}, *element["oneof"]]
    ui_model = test_ui_model(element, extra_types=_POLY_TYPES)
    assert set(ui_model["children"]) == {"name", "orcid", "ror"}
    assert set(ui_model["variants"]) == {"person", "organization"}
