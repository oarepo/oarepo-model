# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pytest

from oarepo_model.api import model


def test_no_presets():
    with pytest.raises(ValueError, match="At least one preset must be provided"):
        model(
            name="empty_model",
            presets=[],
            version="1.0.0",
            types=[],
        )
