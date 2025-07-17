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
from invenio_files_rest.models import Bucket
from sqlalchemy.orm import declared_attr
from sqlalchemy_utils.types import UUIDType, ChoiceType

from oarepo_model.customizations import (
    AddMixins,
    Customization,
)
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset
from invenio_rdm_records.records.systemfields.deletion_status import (
    RecordDeletionStatusEnum,
)

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class RDMRecordMetadataWithFilesPreset(Preset):
    """
    Preset for records_resources.records
    """

    modifies = ["RecordMetadata"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        class RDMRecordMetadataWithFilesMixin:
            __table_args__ = {"extend_existing": True}
            deletion_status = db.Column(
                ChoiceType(RecordDeletionStatusEnum, impl=db.String(1)),
                nullable=False,
                default=RecordDeletionStatusEnum.PUBLISHED.value,
            )
            media_bucket_id = db.Column(UUIDType, db.ForeignKey(Bucket.id)) #index=true?

            @declared_attr
            def media_bucket(cls):
                return db.relationship(Bucket, foreign_keys=[cls.media_bucket_id])

        yield AddMixins(
            "RecordMetadata",
            RDMRecordMetadataWithFilesMixin,
        )