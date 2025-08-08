#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for creating RDM record db metadata.

This module provides a preset that modifies record db metadata to RDM compatibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_db import db
from invenio_files_rest.models import Bucket
from invenio_rdm_records.records.systemfields.deletion_status import (
    RecordDeletionStatusEnum,
)
from sqlalchemy.orm import declared_attr
from sqlalchemy_utils.types import ChoiceType, UUIDType

from oarepo_model.customizations import (
    AddClassField,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


def media_bucket(cls):  # noqa
    return db.relationship(Bucket, foreign_keys=[cls.media_bucket_id])


class RDMRecordMetadataWithFilesPreset(Preset):
    """Preset for records_resources.records."""

    modifies = ("RecordMetadata",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClassField("RecordMetadata", "media_bucket_id", db.Column(UUIDType, db.ForeignKey(Bucket.id)))
        yield AddClassField("RecordMetadata", "media_bucket", declared_attr(media_bucket))
        yield AddClassField(
            "RecordMetadata",
            "deletion_status",
            db.Column(
                ChoiceType(RecordDeletionStatusEnum, impl=db.String(1)),
                nullable=False,
                default=RecordDeletionStatusEnum.PUBLISHED.value,
            ),
        )
