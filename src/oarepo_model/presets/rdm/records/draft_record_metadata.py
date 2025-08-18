#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for creating RDM draft db metadata.

This module provides a preset that modifies draft db metadata to RDM compatibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_db import db
from invenio_rdm_records.records.systemfields.deletion_status import (
    RecordDeletionStatusEnum,
)
from sqlalchemy_utils.types import ChoiceType

from oarepo_model.customizations import (
    AddClassField,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMDraftRecordMetadataWithFilesPreset(Preset):
    """Preset for records_resources.records."""

    modifies = ("DraftMetadata",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClassField(
            "RecordMetadata",
            "deletion_status",
            db.Column(
                ChoiceType(RecordDeletionStatusEnum, impl=db.String(1)),
                nullable=False,
                default=RecordDeletionStatusEnum.PUBLISHED.value,
            ),
        )
