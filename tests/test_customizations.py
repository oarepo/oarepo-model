#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations import (
    AddJSONFile,
    AddModule,
    AddToDictionary,
    AddToList,
    AddToModule,
    IndexSettings,
)


def test_add_to_dictionary():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    builder.add_dictionary("ADict")

    AddToDictionary("ADict", key="a", value="b").apply(builder, model)
    assert builder.get_dictionary("ADict")["a"] == "b"

    with pytest.raises(ValueError, match="Key 'a' already exists in dictionary 'ADict'"):
        AddToDictionary("ADict", key="a", value="b").apply(builder, model)

    AddToDictionary("ADict", key="a", value="c", exists_ok=True).apply(builder, model)
    assert builder.get_dictionary("ADict")["a"] == "c"

    AddToDictionary("ADict", key="a", value="d", patch=True).apply(builder, model)
    assert builder.get_dictionary("ADict")["a"] == "d"

    AddToDictionary("BDict", {"a": "1"}).apply(builder, model)
    assert builder.get_dictionary("BDict")["a"] == "1"


def test_add_to_list():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    builder.add_list("AList")

    AddToList("AList", "item1").apply(builder, model)
    assert list(builder.get_list("AList")) == ["item1"]

    AddToList("AList", "item2").apply(builder, model)
    assert list(builder.get_list("AList")) == ["item1", "item2"]

    with pytest.raises(ValueError, match="already exists in list"):
        AddToList("AList", "item1").apply(builder, model)

    AddToList("AList", "item1", exists_ok=True).apply(builder, model)
    assert list(builder.get_list("AList")) == ["item1", "item2", "item1"]

    AddToList("BList", ["item3"]).apply(builder, model)
    assert list(builder.get_list("BList")) == [["item3"]]


def test_add_to_module():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    builder.add_module("AModule")

    AddToModule("AModule", "item1", 1).apply(builder, model)
    assert builder.get_module("AModule").item1 == 1

    AddToModule("AModule", "item2", 2).apply(builder, model)
    assert builder.get_module("AModule").item2 == 2

    with pytest.raises(ValueError, match="already exists in module"):
        AddToModule("AModule", "item1", 1).apply(builder, model)

    AddToModule("AModule", "item1", 3, exists_ok=True).apply(builder, model)
    assert builder.get_module("AModule").item1 == 3


def test_index_customizations():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    AddModule("blah").apply(builder, model)
    AddJSONFile("record-mapping", "blah", "blah.json", {}, exists_ok=True).apply(builder, model)
    IndexSettings({"a": 1, "b": [1, 2], "c": {"d": 4, "e": 5}, "f": "blah"}).apply(builder, model)
    assert json.loads(builder.get_file("record-mapping").content) == {
        "settings": {"a": 1, "b": [1, 2], "c": {"d": 4, "e": 5}, "f": "blah"}
    }

    IndexSettings({"a": 5, "b": [4], "c": {"d": 1, "e": None}, "f": "abc"}).apply(builder, model)
    assert json.loads(builder.get_file("record-mapping").content) == {
        "settings": {
            "a": 5,
            "b": [1, 2, 4],
            "c": {"d": 1},
            "f": "abc",
        }
    }
    IndexSettings({"a": 1}).apply(builder, model)
    assert json.loads(builder.get_file("record-mapping").content) == {
        "settings": {
            "a": 5,
            "b": [1, 2, 4],
            "c": {"d": 1},
            "f": "abc",
        }
    }
