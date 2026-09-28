# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Presets for adding custom fields schema support to services.

This module provides the RecordCustomFieldsSchemaPreset and RecordCustomFieldsUISchemaPreset
that add custom fields schema mixins to the record schema and the record UI schema.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, override

import marshmallow
from invenio_records_resources.services.custom_fields import CustomFieldsSchema, CustomFieldsSchemaUI
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
    """Add custom fields to the record schema."""

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


class RecordCustomFieldsUISchemaPreset(Preset):
    """Add custom fields to the record UI schema."""

    modifies = ("RecordUISchema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        custom_fields_key = model.uppercase_name + "_CUSTOM_FIELDS"

        class CustomFieldsUIMixin(marshmallow.Schema):
            # the UI schema dumps a dict, not a record, so plain Nested (as in RDM's UI schema)
            custom_fields = marshmallow.fields.Nested(
                partial(CustomFieldsSchemaUI, fields_var=custom_fields_key),
            )

        yield PrependMixin(
            "RecordUISchema",
            CustomFieldsUIMixin,
        )
