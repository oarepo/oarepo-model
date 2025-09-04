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

from .drafts_ui_links import DraftsUILinksPreset
from .records_ui_links import RecordUILinksPreset

ui_links_preset = [RecordUILinksPreset, DraftsUILinksPreset]
