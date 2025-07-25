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
    DraftMetadataBase,
    ParentRecordMixin,
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


class DraftMetadataPreset(Preset):
    """
    Preset for draft record metadata class
    """

    provides = [
        "DraftMetadata",
    ]
    depends_on = [
        "ParentRecordMetadata",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        class DraftMetadataMixin:
            __tablename__ = f"{builder.model.base_name}_draft_metadata"
            __table_args__ = {"extend_existing": True}
            __parent_record_model__ = dependencies["ParentRecordMetadata"]

        yield AddClass("DraftMetadata")
        yield AddBaseClasses(
            "DraftMetadata", db.Model, DraftMetadataBase, ParentRecordMixin
        )
        yield AddMixins("DraftMetadata", DraftMetadataMixin)
