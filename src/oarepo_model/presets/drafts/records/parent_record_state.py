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

from invenio_db import db
from invenio_drafts_resources.records import (
    ParentRecordStateMixin as InvenioParentRecordStateMixin,
)

from oarepo_model.customizations import (
    AddBaseClasses,
    AddClass,
    AddMixins,
    Customization,
)
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class ParentRecordStatePreset(Preset):
    """
    Preset for parent record state class
    """

    provides = [
        "ParentRecordState",
    ]
    depends_on = [
        "ParentRecordMetadata",
        "RecordMetadata",
        "DraftMetadata",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        class ParentRecordStateMixin:
            __record_model__ = dependencies["RecordMetadata"]
            __draft_model__ = dependencies["DraftMetadata"]
            __parent_record_model__ = dependencies["ParentRecordMetadata"]
            __tablename__ = f"{builder.model.base_name}_parent_record_state"
            __table_args__ = {"extend_existing": True}

        yield AddClass("ParentRecordState")
        yield AddBaseClasses(
            "ParentRecordState", db.Model, InvenioParentRecordStateMixin
        )
        yield AddMixins("ParentRecordState", ParentRecordStateMixin)
