#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""UI schema components for Invenio record serialization.

This module provides UI schema classes and presets for serializing Invenio records
in user interface contexts. It includes:

- InvenioRecordUISchema: A base UI schema class with RDM-compatible top-level fields
  including localized date formatting, access status, and tombstone information
- RecordUISchemaPreset: A preset that applies the UI schema to the model builder
- Utility functions for generating UI Marshmallow schemas from various schema types

The schemas are designed to be compatible with Invenio-RDM and provide consistent
formatting for record data in web interfaces.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

import marshmallow
from flask_resources import BaseObjectSchema
from invenio_rdm_records.resources.serializers.ui.fields import AccessStatusField
from invenio_rdm_records.resources.serializers.ui.schema import (
    TombstoneSchema,
)
from marshmallow import fields
from marshmallow_utils.fields import FormatDate

from oarepo_model.customizations import AddClass, Customization, PrependMixin
from oarepo_model.datatypes.collections import ObjectDataType
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class InvenioRecordUISchema(BaseObjectSchema):
    """UI schema for Invenio records.

    This schema should be RDM compatible on the top-level fields.
    """

    created_date_l10n_short = FormatDate(attribute="created", format="short")
    created_date_l10n_medium = FormatDate(attribute="created", format="medium")
    created_date_l10n_long = FormatDate(attribute="created", format="long")
    created_date_l10n_full = FormatDate(attribute="created", format="full")

    updated_date_l10n_short = FormatDate(attribute="updated", format="short")
    updated_date_l10n_medium = FormatDate(attribute="updated", format="medium")
    updated_date_l10n_long = FormatDate(attribute="updated", format="long")
    updated_date_l10n_full = FormatDate(attribute="updated", format="full")

    # TODO: custom fields

    # TODO: move access_status and tombstone to RDM
    access_status = AccessStatusField(attribute="access")
    tombstone = fields.Nested(TombstoneSchema, attribute="tombstone")


class RecordUISchemaPreset(Preset):
    """Preset for record service class."""

    provides = ("RecordUISchema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass("RecordUISchema", clazz=InvenioRecordUISchema)

        if model.record_type is not None:
            yield PrependMixin(
                "RecordUISchema",
                get_ui_marshmallow_schema(builder, model.record_type),
            )


def get_ui_marshmallow_schema(builder: InvenioModelBuilder, schema_type: Any) -> type[marshmallow.Schema]:
    """Get the UI Marshmallow schema for the given schema type."""
    base_schema: type[marshmallow.Schema]
    if isinstance(schema_type, (str, dict)):
        datatype = builder.type_registry.get_type(schema_type)
        base_schema = cast("Any", datatype).create_ui_marshmallow_schema(
            {} if isinstance(schema_type, str) else schema_type
        )
    elif isinstance(schema_type, ObjectDataType):
        base_schema = schema_type.create_ui_marshmallow_schema({})
    elif issubclass(schema_type, marshmallow.Schema):
        base_schema = schema_type
    else:
        raise TypeError(f"Invalid schema type: {schema_type}. Expected str, dict or None.")
    return base_schema
