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
    PatchIndexSettings,
)


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
