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


class MetadataJSONSchemaPreset(Preset):
    """
    Preset for record service class.
    """

    modifies = ["RECORD_JSON_SCHEMA_PATH"]
    provides = ["metadata-json-schema"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        if model.metadata_type is not None:
            from .record_json_schema import get_json_schema

            jsonschema = get_json_schema(builder, model.metadata_type)

            yield PatchJSONFile(
                "jsonschemas",
                f"{model.base_name}-v{model.version}.json",
                {
                    "properties": {
                        "metadata": jsonschema,
                    }
                },
            )
