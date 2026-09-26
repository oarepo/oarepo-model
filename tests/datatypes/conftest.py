# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pytest


@pytest.fixture
def datatype_registry():
    """Fixture to provide a datatype registry."""
    from oarepo_model.datatypes.registry import DataTypeRegistry

    registry = DataTypeRegistry()
    registry.load_entry_points()
    return registry
