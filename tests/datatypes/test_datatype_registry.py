#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from oarepo_model.datatypes.registry import DataTypeRegistry
from oarepo_model.datatypes.strings import KeywordDataType


def test_datatype_registry():
    dt = DataTypeRegistry()
    dt.load_entry_points()
    assert "keyword" in dt.types
    assert isinstance(dt.types["keyword"], KeywordDataType)
