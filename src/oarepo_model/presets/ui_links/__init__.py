# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""UI presets for generating ui.json for Jinja components and JavaScript."""

from __future__ import annotations

from .drafts_ui_links import DraftsUILinksPreset
from .ext import UILinksFeaturePreset
from .records_ui_links import RecordUILinksPreset

ui_links_preset = [
    RecordUILinksPreset,
    DraftsUILinksPreset,
    # feature
    UILinksFeaturePreset,
]
