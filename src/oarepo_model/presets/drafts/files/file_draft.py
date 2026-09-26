# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for draft file record model.

This module provides the FileDraftPreset that creates
draft file record API classes for handling file operations.
"""

from __future__ import annotations

from oarepo_model.presets.records_resources.files.file_record import file_record_preset

FileDraftPreset = file_record_preset("FileDraft", model_cls_name="FileDraftMetadata", record_cls_name="Draft")
