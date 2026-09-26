# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for adding custom fields support to record mappings.

This module provides the CustomFieldsMappingPreset that adds
custom fields mapping configuration to published records in Opensearch.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import Customization, PatchJSONFile
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class CustomFieldsMappingPreset(Preset):
    """Preset for adding custom fields to record mappings."""

    depends_on = ("record-mapping",)

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
                    "custom_fields": {
                        "type": "object",
                        "dynamic": True,
                    },
                },
            },
        }

        yield PatchJSONFile(
            "record-mapping",
            file_mapping,
        )
