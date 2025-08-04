#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate record schema class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

import marshmallow
from invenio_records_resources.services.records.schema import BaseRecordSchema

from oarepo_model.customizations import AddClass, AddMixins, Customization
from oarepo_model.datatypes.collections import ObjectDataType
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordSchemaPreset(Preset):
    """Preset for record service class."""

    provides = ("RecordSchema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass("RecordSchema", clazz=BaseRecordSchema)

        if model.record_type is not None:
            yield AddMixins(
                "RecordSchema",
                get_marshmallow_schema(builder, model.record_type),
            )


def get_marshmallow_schema(
    builder: InvenioModelBuilder,
    schema_type: Any,
) -> type[marshmallow.Schema]:
    """Get the marshmallow schema for a given schema type."""
    base_schema: type[marshmallow.Schema]
    if isinstance(schema_type, (str, dict)):
        datatype = builder.type_registry.get_type(schema_type)
        base_schema = cast("Any", datatype).create_marshmallow_schema(
            {} if isinstance(schema_type, str) else schema_type,
        )
    elif isinstance(schema_type, ObjectDataType):
        base_schema = schema_type.create_marshmallow_schema({})
    elif issubclass(schema_type, marshmallow.Schema):
        base_schema = schema_type
    else:
        raise TypeError(
            f"Invalid schema type: {schema_type}. Expected str, dict or None.",
        )
    return base_schema
