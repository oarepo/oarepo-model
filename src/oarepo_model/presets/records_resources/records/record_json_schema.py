#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator, cast

from deepmerge import always_merger

from oarepo_model.customizations import AddJSONFile, Customization
from oarepo_model.datatypes.collections import ObjectDataType
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class RecordJSONSchemaPreset(Preset):
    """
    Preset for record service class.
    """

    modifies = ["jsonschemas"]
    provides = ["metadata-json-schema"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        if model.record_type is not None:
            jsonschema = get_json_schema(builder, model.record_type)
        else:
            jsonschema = {}

        jsonschema = always_merger.merge(
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "id": "local://records/record-v1.0.0.json",
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "files": {
                        "type": "object",
                        "properties": {
                            "enabled": {"type": "boolean"},
                        },
                    },
                },
            },
            jsonschema,
        )

        yield AddJSONFile(
            "metadata-json-schema",
            "jsonschemas",
            f"{model.base_name}-v{model.version}.json",
            jsonschema,
        )


def get_json_schema(builder: InvenioModelBuilder, schema_type: Any) -> dict[str, Any]:
    if isinstance(schema_type, (str, dict)):
        datatype = builder.type_registry.get_type(schema_type)
        base_schema = cast(Any, datatype).create_json_schema(
            {} if isinstance(schema_type, str) else schema_type
        )
    elif isinstance(schema_type, ObjectDataType):
        base_schema = schema_type.create_json_schema({})
    else:
        raise ValueError(
            f"Invalid schema type: {schema_type}. Expected str, dict or None."
        )
    return base_schema
