#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for enabling draft support in record schema.

This module provides a preset that changes the base record schema from
BaseRecordSchema to the draft-enabled RecordSchema. This allows the schema
to handle draft-specific validation and serialization requirements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.services.records.schema import RecordSchema
from invenio_records_resources.services.records.schema import BaseRecordSchema
from marshmallow_utils.fields import NestedAttribute

from oarepo_model.customizations import Customization, PrependMixin, ReplaceBaseClass
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftRecordSchemaPreset(Preset):
    """Preset for record service class."""

    depends_on = ("ParentRecordSchema",)
    modifies = ("RecordSchema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        # change the base schema from BaseRecordSchema to draft enabled RecordSchema
        # do not fail, for example if user provided their own RecordSchema
        class ParentRecordSchemaMixin:
            parent = NestedAttribute(dependencies["ParentRecordSchema"])

        yield ReplaceBaseClass("RecordSchema", BaseRecordSchema, RecordSchema)
        yield PrependMixin("RecordSchema", ParentRecordSchemaMixin)
