# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Custom fields presets for OARepo models.

This package provides presets for adding custom fields functionality to OARepo models,
including support for extensible record schemas and dynamic field configurations.
"""

from __future__ import annotations

from invenio_records_resources import __version__

from oarepo_model.presets.records_resources.ext import feature_preset

CustomFieldsFeaturePreset = feature_preset("custom-fields", __version__)
