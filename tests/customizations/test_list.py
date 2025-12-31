#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations import (
    AddToList,
)


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
