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

import marshmallow as ma
import pytest
from invenio_records_resources.services.records.components import ServiceComponent

from oarepo_model.api import model
from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations import (
    AddJSONFile,
    AddModule,
    AddServiceComponent,
    AddToDictionary,
    AddToList,
    AddToModule,
    PatchIndexSettings,
    PrependMixin,
)
from oarepo_model.presets.records_resources import records_resources_preset


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
    PatchIndexSettings({"a": 1, "b": [1, 2], "c": {"d": 4, "e": 5}, "f": "blah"}).apply(builder, model)
    assert json.loads(builder.get_file("record-mapping").content) == {
        "settings": {"a": 1, "b": [1, 2], "c": {"d": 4, "e": 5}, "f": "blah"}
    }

    PatchIndexSettings({"a": 5, "b": [4], "c": {"d": 1, "e": None}, "f": "abc"}).apply(builder, model)
    assert json.loads(builder.get_file("record-mapping").content) == {
        "settings": {
            "a": 5,
            "b": [1, 2, 4],
            "c": {"d": 1},
            "f": "abc",
        }
    }
    PatchIndexSettings({"a": 1}).apply(builder, model)
    assert json.loads(builder.get_file("record-mapping").content) == {
        "settings": {
            "a": 5,
            "b": [1, 2, 4],
            "c": {"d": 1},
            "f": "abc",
        }
    }


class TestServiceComponent(ServiceComponent):
    """Test service component."""


def test_add_service_component():
    m = model(
        name="test_add_service_component",
        version="1.0.0",
        presets=[
            records_resources_preset,
        ],
        customizations=[
            AddServiceComponent(TestServiceComponent),
        ],
    )

    # ideally check whether the component actually ends in the service components list after app init
    assert len([c for c in m.record_service_components if issubclass(c, TestServiceComponent)]) == 1


def test_metadata_add_mixin(model_types):
    class TestMixin:
        height = ma.fields.Float()

    m = model(
        name="metadata_mixin_test",
        version="1.0.0",
        presets=[
            records_resources_preset,
        ],
        types=[model_types],
        customizations=[
            PrependMixin("MetadataSchema", TestMixin),
        ],
        metadata_type="Metadata",
    )
    metadata_schema_cls = m.RecordSchema().fields["metadata"].nested()
    assert issubclass(metadata_schema_cls, TestMixin)
    assert isinstance(metadata_schema_cls().fields["height"], ma.fields.Float)
