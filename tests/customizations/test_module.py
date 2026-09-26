# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations import (
    AddToModule,
)


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
