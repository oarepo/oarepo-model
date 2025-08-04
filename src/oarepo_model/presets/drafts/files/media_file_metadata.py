#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for creating media file metadata database model.

This module provides a preset that creates a MediaFileMetadata class for
storing media file metadata in the database. It includes table structure,
indexes for efficient querying, and relationships to record models through
the FileRecordModelMixin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_db import db
from invenio_records.models import RecordMetadataBase
from sqlalchemy.orm import declared_attr

from oarepo_model.customizations import (
    AddBaseClasses,
    AddClass,
    AddClassField,
    AddMixins,
    Customization,
)
from oarepo_model.presets import Preset

from ...records_resources.files.file_record_model_mixin import (
    FileRecordModelMixin,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class MediaFileMetadataPreset(Preset):
    """Preset for file metadata class."""

    provides = ("MediaFileMetadata",)

    depends_on = (
        # need to have this dependency because of __record_model_cls__ attribute
        "RecordMetadata",
    )

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class MediaFileMetadataMixin:
            __tablename__ = f"{builder.model.base_name}_media_files"
            __record_model_cls__ = dependencies.get("RecordMetadata")

        @declared_attr  # type: ignore[misc]
        def __table_args__(cls):  # noqa declared attr is class method
            """Table args."""
            return (
                db.Index(
                    f"uidx_{cls.__tablename__}_record_id_key",
                    "record_id",
                    "key",
                    unique=True,
                ),
                db.Index(
                    f"uidx_{cls.__tablename__}_record_id",
                    "record_id",
                ),
                db.Index(
                    f"uidx_{cls.__tablename__}_object_version_id",
                    "object_version_id",
                ),
                {"extend_existing": True},
            )

        yield AddClass("MediaFileMetadata")
        yield AddClassField("MediaFileMetadata", "__table_args__", __table_args__)
        yield AddBaseClasses(
            "MediaFileMetadata",
            db.Model,
            RecordMetadataBase,
            FileRecordModelMixin,
        )
        yield AddMixins("MediaFileMetadata", MediaFileMetadataMixin)
