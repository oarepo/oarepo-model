# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for creating media file draft API class.

This module provides a preset that creates a MediaFileDraft class based on
Invenio's FileRecord API. This class represents individual media files
attached to draft records during the editing process and provides methods
for media file manipulation and metadata access.
"""

from __future__ import annotations

from oarepo_model.presets.records_resources.files.file_record import file_record_preset

MediaFileDraftPreset = file_record_preset(
    "MediaFileDraft",
    model_cls_name="MediaFileDraftMetadata",
    record_cls_name="DraftMediaFiles",
)
