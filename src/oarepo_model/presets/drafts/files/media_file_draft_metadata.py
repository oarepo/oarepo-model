# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for creating media file draft metadata database model.

This module provides a preset that creates a MediaFileDraftMetadata class
for storing media file metadata of draft records in the database. It includes
table structure, indexes for efficient querying, and relationships to draft
models through the FileRecordModelMixin.
"""

from __future__ import annotations

from oarepo_model.presets.records_resources.files.file_metadata import file_metadata_preset

MediaFileDraftMetadataPreset = file_metadata_preset(
    "MediaFileDraftMetadata",
    table_suffix="_draft_media_files",
    record_model_cls_name="DraftMetadata",
)
