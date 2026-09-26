# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pytest

from oarepo_model.presets.records_resources.services.records.results import (
    _result_components_mixin,
)


def test_components_setter_raises_attribute_error():
    """The generated result mixin's `components` is read-only."""
    mixin = _result_components_mixin(object, "key", {})
    instance = mixin()
    with pytest.raises(AttributeError, match="can't set attribute"):
        instance.components = ()
