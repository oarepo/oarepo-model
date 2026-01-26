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

from oarepo_model.api import model


def test_no_presets():
    with pytest.raises(ValueError, match="At least one preset must be provided"):
        model(
            name="empty_model",
            presets=[],
            version="1.0.0",
            types=[],
        )
