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
from sqlalchemy_utils.types import UUIDType

from oarepo_model.customizations import (
    AddMixins,
    Customization,
)
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class RecordMetadataWithFilesPreset(Preset):
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
        class RecordMetadataWithFilesMixin:
            bucket_id = db.Column(UUIDType, db.ForeignKey(Bucket.id))

            @declared_attr
            def bucket(cls):
                return db.relationship(Bucket)

        yield AddMixins(
            "RecordMetadata",
            RecordMetadataWithFilesMixin,
        )
