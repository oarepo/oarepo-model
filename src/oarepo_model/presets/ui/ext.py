# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""UI presets for generating ui.json for Jinja components and JavaScript."""

from __future__ import annotations

from invenio_records_resources import __version__

from oarepo_model.presets.records_resources.ext import feature_preset

UIFeaturePreset = feature_preset("ui", __version__)
