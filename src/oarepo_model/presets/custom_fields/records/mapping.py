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


class CustomFieldsMappingPreset(Preset):
    """
    Preset for records_resources.records.mapping
    """

    depends_on = ["record-mapping"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        file_mapping = {
            "mappings": {
                "properties": {
                    "custom_fields": {
                        "type": "object",
                        "dynamic": True,
                    },
                }
            }
        }

        yield PatchJSONFile(
            "record-mapping",
            file_mapping,
        )
