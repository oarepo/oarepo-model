# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations import (
    AddToList,
)
from oarepo_model.errors import PartialNotFoundError


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

    builder.add_list("BList")
    AddToList("BList", ["item3"]).apply(builder, model)
    assert list(builder.get_list("BList")) == [["item3"]]


def test_add_to_list_missing_list_raises():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)

    with pytest.raises(PartialNotFoundError, match="NoList"):
        AddToList("NoList", "item1").apply(builder, model)
