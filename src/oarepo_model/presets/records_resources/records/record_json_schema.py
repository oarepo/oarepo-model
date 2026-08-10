#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate json shema of an invenio record."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from deepmerge import always_merger

from oarepo_model.customizations import AddJSONFile, AddModule, Customization
from oarepo_model.datatypes.collections import ObjectDataType
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordJSONSchemaPreset(Preset):
    """Preset for record service class."""

    modifies = ("jsonschemas",)
    provides = ("record-jsonschema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        jsonschema = get_json_schema(builder, model.record_type) if model.record_type is not None else {}

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
            "record-jsonschema",
            "jsonschemas",
            f"{model.base_name}-v{model.version}.json",
            jsonschema,
        )
        # Same json schema, stored a second time under a stable, version-independent
        # key so that it can be located in the model's namespace __files__ without
        # having to know/reconstruct the {base_name}-v{version}.json naming scheme
        # (e.g. from a lazily-resolved self-referencing relation). Both entries
        # share the same "jsonschema" dict object, so later patches to the
        # "record-jsonschema" file (which mutate that dict in place) are
        # reflected here too. Stored in a separate "internal" module rather than
        # under "jsonschemas" for the same reason the mapping is (see
        # record_mapping.py) - "jsonschemas" is walked as a whole elsewhere.
        yield AddModule("internal", exists_ok=True)
        yield AddJSONFile(
            "record-primary-jsonschema",
            "internal",
            "primary_jsonschema.json",
            jsonschema,
        )


def get_json_schema(builder: InvenioModelBuilder, schema_type: Any) -> dict[str, Any]:
    """Get the JSON schema for a given schema type."""
    base_schema: dict[str, Any]
    if isinstance(schema_type, (str, dict)):
        datatype = builder.type_registry.get_type(schema_type)
        base_schema = cast("Any", datatype).create_json_schema(
            {} if isinstance(schema_type, str) else schema_type,
        )
    elif isinstance(schema_type, ObjectDataType):
        base_schema = schema_type.create_json_schema({})
    else:
        raise TypeError(
            f"Invalid schema type: {schema_type}. Expected str, dict or None.",
        )
    return base_schema
