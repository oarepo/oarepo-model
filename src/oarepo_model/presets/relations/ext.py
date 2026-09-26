# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""A module for defining presets for model relations."""

from __future__ import annotations

from invenio_records_resources import __version__

from oarepo_model.presets.records_resources.ext import feature_preset

RelationsFeaturePreset = feature_preset("relations", __version__)
