#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from oarepo_model.customizations import Customization, PatchJSONFile
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class MetadataMappingPreset(Preset):
    """
    Preset for record service class.
    """

    modifies = ["RECORD_MAPPING_PATH"]
    provides = ["metadata-mapping"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        if model.metadata_type is not None:
            from .record_mapping import get_mapping

            mapping = get_mapping(builder, model.metadata_type)

            yield PatchJSONFile(
                "mappings",
                f"os-v2/{model.base_name}/metadata-v{model.version}.json",
                {
                    "mappings": {
                        "properties": {
                            "metadata": mapping,
                        }
                    }
                },
            )
