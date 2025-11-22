#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for creating FileMetadata database model.

This module provides a preset that creates a FileMetadata class for storing
file metadata in the database. It includes table structure, indexes for
efficient querying, and relationships to record models through the
FileRecordModelMixin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_db import db
from invenio_records.models import RecordMetadataBase
from invenio_records_resources.records.models import FileRecordModelMixin

from oarepo_model.customizations import (
    AddBaseClass,
    AddClass,
    AddClassField,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class FileMetadataPreset(Preset):
    """Preset for FileMetadata class."""

    provides = ("FileMetadata",)

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
        yield AddClass("FileMetadata")
        yield AddClassField("FileMetadata", "__tablename__", f"{builder.model.base_name}_files")
        yield AddClassField("FileMetadata", "__record_model_cls__", dependencies.get("RecordMetadata"))
        yield AddBaseClass("FileMetadata", db.Model)
        yield AddBaseClass("FileMetadata", RecordMetadataBase)
        yield AddBaseClass("FileMetadata", FileRecordModelMixin)
