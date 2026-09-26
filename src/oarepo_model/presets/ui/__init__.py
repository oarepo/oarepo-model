# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""UI presets for generating ui.json for Jinja components and JavaScript."""

from __future__ import annotations

from .ext import UIFeaturePreset
from .ui_ext import UIExtPreset
from .ui_metadata import UIMetadataPreset
from .ui_record import UIRecordPreset

ui_preset = [
    UIRecordPreset,
    UIMetadataPreset,
    UIExtPreset,
    # feature
    UIFeaturePreset,
]
