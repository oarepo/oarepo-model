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
from deepmerge import always_merger

from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations import AddJSONFile, PatchIndexPropertyMapping
from oarepo_model.datatypes.relations import LazyMapping
from oarepo_model.utils import resolve_file_content

TARGET_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "metadata": {
                "type": "object",
                "properties": {"title": {"type": "keyword"}},
            },
        }
    }
}


@pytest.fixture
def relation_mapping(datatype_registry):
    """Mapping of a pid-relation whose target model is not built yet."""
    element = {
        "type": "pid-relation",
        "model": "unbuilt_model",
        "keys": ["id", "metadata.title"],
    }
    mapping = datatype_registry.get_type(element).create_mapping(element)
    assert isinstance(mapping["properties"], LazyMapping)
    # stand in for the target model's namespace file, which needs a running app
    mapping["properties"]._load_json = lambda: TARGET_MAPPING
    return mapping


def test_deepmerge_drops_lazy_mapping_node(relation_mapping):
    base = {"properties": {"related": relation_mapping}}

    always_merger.merge(base, {"properties": {"related": {"properties": {"extra": {"type": "keyword"}}}}})

    merged = base["properties"]["related"]["properties"]
    assert "extra" in merged
    assert set(merged) >= {"id", "metadata", "@v"}


def test_patch_index_property_mapping_keeps_relation_keys(relation_mapping):
    model = MagicMock()
    builder = InvenioModelBuilder(model, MagicMock())
    builder.add_module("mappings")
    AddJSONFile(
        "record-mapping",
        "mappings",
        "os-v2/record-metadata.json",
        {"mappings": {"properties": {"related": relation_mapping}}},
    ).apply(builder, model)

    PatchIndexPropertyMapping("related", {"properties": {"extra": {"type": "keyword"}}}).apply(builder, model)

    content = json.loads(resolve_file_content(builder.get_file("record-mapping").content))
    merged = content["mappings"]["properties"]["related"]["properties"]
    assert "extra" in merged
    assert set(merged) >= {"id", "metadata", "@v"}
