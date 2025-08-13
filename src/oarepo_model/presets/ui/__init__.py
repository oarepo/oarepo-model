#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""UI presets for generating ui.json for Jinja components and JavaScript."""

from __future__ import annotations

from .ui_ext import UIExtPreset
from .ui_metadata import UIMetadataPreset
from .ui_record import UIRecordPreset

ui_presets = [
    UIRecordPreset,
    UIMetadataPreset,
    UIExtPreset,
]
