#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for creating RDM record marshmallow schema.

This module provides a preset that modifies record marshmallow schema to RDM compatibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.services.records.schema import RecordSchema

# TODO: from oarepo_runtime.services.schema.marshmallow import RDMBaseRecordSchema
from invenio_rdm_records.services.schemas.record import RDMRecordSchema as RDMBaseRecordSchema

from oarepo_model.customizations import ChangeBase, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMRecordSchemaPreset(Preset):
    """Preset for record service class."""

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
        yield ChangeBase("RecordSchema", RecordSchema, RDMBaseRecordSchema)
