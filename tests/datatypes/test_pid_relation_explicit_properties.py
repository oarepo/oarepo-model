#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import pytest

from oarepo_model.datatypes.relations import (
    LazyModelJSONFile,
    LazyProxiedMarshmallowSchema,
    LazyUIModelChildren,
)

PROPERTIES = {
    "id": {"type": "keyword"},
    "metadata": {
        "type": "object",
        "properties": {"title": {"type": "keyword"}},
    },
}


def _element(**target: object) -> dict:
    # a pid-relation whose target is not importable at build time
    # (self-referencing style), with 'properties' declared explicitly
    return {
        "type": "pid-relation",
        "keys": ["id", "metadata.title"],
        "properties": PROPERTIES,
        **target,
    }


@pytest.mark.parametrize(
    "target",
    [
        {"record_cls": "runtime_models_unbuilt_model:Record"},
        {"model": "unbuilt_model"},
    ],
)
def test_explicit_properties_take_precedence_over_lazy(datatype_registry, target):
    """Declared 'properties' must be used even when the relation's target is not built yet.

    Regression test: the lazy create_* paths used to ignore a declared
    'properties' key - record_cls-based elements failed the build with
    ValueError("'model' key is required for lazy mapping"), while model-based
    elements silently resolved the target's default types instead of the
    declared ones.
    """
    element = _element(**target)
    datatype = datatype_registry.get_type(element)

    mapping = datatype.create_mapping(element)
    assert not isinstance(mapping["properties"], LazyModelJSONFile)
    assert set(mapping["properties"]) == {"id", "metadata"}
    assert "title" in mapping["properties"]["metadata"]["properties"]

    json_schema = datatype.create_json_schema(element)
    assert not isinstance(json_schema["properties"], LazyModelJSONFile)
    assert "title" in json_schema["properties"]["metadata"]["properties"]

    record_schema = datatype.create_marshmallow_schema(element)
    assert not issubclass(record_schema, LazyProxiedMarshmallowSchema)
    assert set(record_schema().fields) >= {"id", "metadata"}

    ui_schema = datatype.create_ui_marshmallow_schema(element)
    assert not issubclass(ui_schema, LazyProxiedMarshmallowSchema)
    assert "metadata" in ui_schema().fields

    ui_model = datatype.create_ui_model(element, ["a"])
    assert not isinstance(ui_model["children"], LazyUIModelChildren)
    assert set(ui_model["children"]) >= {"id", "metadata"}
