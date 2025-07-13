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

from invenio_drafts_resources.services.records.schema import RecordSchema
from invenio_records_resources.services.records.schema import BaseRecordSchema

from oarepo_model.customizations import ChangeBase, Customization
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class DraftRecordSchemaPreset(Preset):
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
        # change the base schema from BaseRecordSchema to draft enabled RecordSchema
        # do not fail, for example if user provided their own RecordSchema
        yield ChangeBase("RecordSchema", BaseRecordSchema, RecordSchema, fail=False)
