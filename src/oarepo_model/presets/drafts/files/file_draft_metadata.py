# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for draft file metadata database model.

This module provides the FileDraftMetadataPreset that creates
database metadata model classes for draft file records.
"""

from __future__ import annotations

from oarepo_model.presets.records_resources.files.file_metadata import file_metadata_preset

FileDraftMetadataPreset = file_metadata_preset(
    "FileDraftMetadata",
    table_suffix="_draft_files",
    record_model_cls_name="DraftMetadata",
)
