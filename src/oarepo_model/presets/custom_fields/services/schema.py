#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, Generator

import marshmallow
from invenio_records_resources.services.custom_fields import CustomFieldsSchema
from marshmallow_utils.fields import (
    NestedAttribute,
)

from oarepo_model.customizations import AddMixins, Customization
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class RecordCustomFieldsSchemaPreset(Preset):
    """
    Preset for record service class.
    """

    modifies = ["RecordSchema"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        custom_fields_key = model.uppercase_name + "_CUSTOM_FIELDS"

        class CustomFieldsMixin(marshmallow.Schema):
            custom_fields = NestedAttribute(
                partial(CustomFieldsSchema, fields_var=custom_fields_key)
            )

        yield AddMixins(
            "RecordSchema",
            CustomFieldsMixin,
        )
