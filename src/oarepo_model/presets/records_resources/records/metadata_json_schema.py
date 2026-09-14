# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to generate metadata JSON schema for records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import Customization, PatchJSONFile
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class MetadataJSONSchemaPreset(Preset):
    """Preset for record service class."""

    modifies = ("record-jsonschema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        if model.metadata_type is not None:
            from .record_json_schema import get_json_schema

            jsonschema = get_json_schema(builder, model.metadata_type)

            yield PatchJSONFile(
                "record-jsonschema",
                {
                    "properties": {
                        "metadata": jsonschema,
                    },
                },
            )
