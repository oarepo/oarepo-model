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


@pytest.fixture
def datatype_registry():
    """Fixture to provide a datatype registry."""
    from oarepo_model.datatypes.registry import DataTypeRegistry

    registry = DataTypeRegistry()
    registry.load_entry_points()
    return registry
