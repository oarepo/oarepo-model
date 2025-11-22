#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for adding custom fields schema support to services.

This module provides the CustomFieldsSchemaPreset that adds
custom fields schema mixins to service schemas for validation.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, override

import marshmallow
from invenio_records_resources.services.custom_fields import CustomFieldsSchema
from marshmallow_utils.fields import (
    NestedAttribute,
)

from oarepo_model.customizations import Customization, PrependMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordCustomFieldsSchemaPreset(Preset):
    """Preset for record service class."""

    modifies = ("RecordSchema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        custom_fields_key = model.uppercase_name + "_CUSTOM_FIELDS"

        class CustomFieldsMixin(marshmallow.Schema):
            custom_fields = NestedAttribute(
                partial(CustomFieldsSchema, fields_var=custom_fields_key),
            )

        yield PrependMixin(
            "RecordSchema",
            CustomFieldsMixin,
        )
