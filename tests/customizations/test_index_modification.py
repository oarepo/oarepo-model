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

from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations import (
    AddJSONFile,
    AddModule,
    PatchIndexMapping,
    PatchIndexPropertyMapping,
    PatchIndexSettings,
)
from oarepo_model.customizations.high_level.index_mapping import recursively_remove_none


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


def test_index_mapping_customizations():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    AddModule("blah").apply(builder, model)
    AddJSONFile(
        "record-mapping",
        "blah",
        "blah.json",
        {
            "mappings": {
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"ignore_above": 100},
                    "c": {
                        "properties": {
                            "d": {"type": "float"},
                            "e": {"index": False, "type": "object"},
                        },
                    },
                    "f": {"type": "keyword"},
                }
            }
        },
        exists_ok=True,
    ).apply(builder, model)
    PatchIndexMapping(
        {
            "properties": {
                "a": {"type": "keyword"},
                "b": {"type": "text"},
                "c": {"properties": {"d": {"type": "integer"}, "e": {"type": "keyword"}}},
                "f": None,
            }
        }
    ).apply(builder, model)
    assert json.loads(builder.get_file("record-mapping").content) == {
        "mappings": {
            "properties": {
                "a": {"type": "keyword"},
                "b": {"type": "text", "ignore_above": 100},
                "c": {
                    "properties": {
                        "d": {"type": "integer"},
                        "e": {"type": "keyword", "index": False},
                    }
                },
            }
        }
    }


def test_patch_index_property_mapping():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    AddModule("blah").apply(builder, model)
    AddJSONFile(
        "record-mapping",
        "blah",
        "blah.json",
        {
            "mappings": {
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"ignore_above": 100},
                    "c": {
                        "properties": {
                            "d": {"type": "float"},
                            "e": {"index": False, "type": "object"},
                        },
                    },
                    "f": {"type": "keyword"},
                }
            }
        },
        exists_ok=True,
    ).apply(builder, model)
    PatchIndexPropertyMapping("a", {"type": "keyword"}).apply(builder, model)
    PatchIndexPropertyMapping("c.d", {"type": "float"}).apply(builder, model)
    PatchIndexPropertyMapping("c.e", None).apply(builder, model)
    assert json.loads(builder.get_file("record-mapping").content) == {
        "mappings": {
            "properties": {
                "a": {
                    "type": "keyword",
                },
                "b": {
                    "ignore_above": 100,
                },
                "c": {
                    "properties": {
                        "d": {
                            "type": "float",
                        },
                    },
                },
                "f": {
                    "type": "keyword",
                },
            }
        }
    }


def test_recursively_remove_none():
    data = {
        "a": 1,
        "b": None,
        "c": {
            "d": 2,
            "e": None,
            "f": {
                "g": None,
                "h": 3,
            },
            "z": [1, None, 2, {"x": None, "y": 3}],
        },
        "i": [1, None, 2, {"j": None, "k": 4}],
    }
    recursively_remove_none(data)
    assert data == {
        "a": 1,
        "c": {
            "d": 2,
            "f": {
                "h": 3,
            },
            "z": [1, 2, {"y": 3}],
        },
        "i": [1, 2, {"k": 4}],
    }
