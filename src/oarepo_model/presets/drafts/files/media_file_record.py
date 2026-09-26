# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for creating media file record API class.

This module provides a preset that creates a MediaFileRecord class based on
Invenio's FileRecord API. This class represents individual media files
attached to published records and provides methods for media file access
and metadata management.
"""

from __future__ import annotations

from oarepo_model.presets.records_resources.files.file_record import file_record_preset

MediaFileRecordPreset = file_record_preset(
    "MediaFileRecord",
    model_cls_name="MediaFileMetadata",
    record_cls_name="RecordMediaFiles",
)
