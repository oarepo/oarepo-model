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

import marshmallow

from oarepo_model.customizations import AddClass, AddMixins, Customization
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class MetadataSchemaPreset(Preset):
    """
    Preset for record service class.
    """

    provides = ["MetadataSchema"]
    modifies = ["RecordSchema"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        if model.metadata_type is not None:
            from .record_schema import get_marshmallow_schema

            metadata_base_schema = get_marshmallow_schema(builder, model.metadata_type)

            yield AddClass("MetadataSchema", clazz=metadata_base_schema)

            class RecordWithMetadataMixin(marshmallow.Schema):
                """Metadata schema for records."""

                metadata = marshmallow.fields.Nested(
                    metadata_base_schema,
                    required=True,
                    allow_none=False,
                    metadata={"description": "Metadata of the record."},
                )

            yield AddMixins("RecordSchema", RecordWithMetadataMixin)
