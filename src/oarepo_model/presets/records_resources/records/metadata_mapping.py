# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to generate metadata mapping for records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import Customization, PatchJSONFile
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class MetadataMappingPreset(Preset):
    """Preset for record service class."""

    modifies = ("record-mapping",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        if model.metadata_type is not None:
            from .record_mapping import get_mapping

            mapping = get_mapping(builder, model.metadata_type)

            yield PatchJSONFile(
                "record-mapping",
                {
                    "mappings": {
                        "properties": {
                            "metadata": {
                                "type": "object",
                                **mapping,
                            },
                        },
                    },
                },
            )
