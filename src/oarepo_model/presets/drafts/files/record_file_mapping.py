# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for adding media files mapping to record Elasticsearch mapping.

This module provides a preset that patches the record Elasticsearch mapping
to include a 'media_files' object with an 'enabled' boolean property. This
ensures that media file metadata is properly indexed and searchable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import Customization, PatchJSONFile
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordFileMappingPreset(Preset):
    """Preset for record service class."""

    modifies = ("record-mapping",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        file_mapping = {
            "mappings": {
                "properties": {
                    "media_files": {
                        "type": "object",
                        "properties": {
                            "enabled": {"type": "boolean"},
                        },
                    },
                },
            },
        }

        yield PatchJSONFile("record-mapping", file_mapping)
