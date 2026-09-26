# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Draft-related presets for Invenio draft/publish workflows.

This module provides presets for implementing draft record functionality,
including file handling, record management, and API blueprints for
draft-enabled Invenio repositories.
"""

from __future__ import annotations

from invenio_drafts_resources import __version__

from oarepo_model.presets.records_resources.ext import feature_preset
from oarepo_model.presets.records_resources.ext_files import (
    RecordWithFilesExtensionProtocol,
)

DraftsFilesFeaturePreset = feature_preset(
    "drafts-files",
    __version__,
    base=RecordWithFilesExtensionProtocol,
)
DraftsRecordsFeaturePreset = feature_preset(
    "drafts-records",
    __version__,
    base=RecordWithFilesExtensionProtocol,
)
