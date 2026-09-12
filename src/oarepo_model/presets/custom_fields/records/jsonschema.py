# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for adding custom fields support to JSON schema definitions.

This module provides the CustomFieldsJSONSchemaPreset that adds
custom fields schema definitions to record JSON schemas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import Customization, PatchJSONFile
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class CustomFieldsJSONSchemaPreset(Preset):
    """Preset for adding custom fields to JSON schema definitions."""

    depends_on = ("record-jsonschema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        jsonschema = {
            "properties": {
                "custom_fields": {
                    "type": "object",
                    "additionalProperties": True,
                },
            },
        }

        yield PatchJSONFile(
            "record-jsonschema",
            jsonschema,
        )
