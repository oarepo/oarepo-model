# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for creating media file metadata database model.

This module provides a preset that creates a MediaFileMetadata class for
storing media file metadata in the database. It includes table structure,
indexes for efficient querying, and relationships to record models through
the FileRecordModelMixin.
"""

from __future__ import annotations

from oarepo_model.presets.records_resources.files.file_metadata import file_metadata_preset

MediaFileMetadataPreset = file_metadata_preset(
    "MediaFileMetadata",
    table_suffix="_media_files",
    record_model_cls_name="RecordMetadata",
)
