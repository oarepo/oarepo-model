#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for draft file metadata database model.

This module provides the FileDraftMetadataPreset that creates
database metadata model classes for draft file records.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_db import db
from invenio_records.models import RecordMetadataBase
from invenio_records_resources.records.models import FileRecordModelMixin

from oarepo_model.customizations import (
    AddBaseClasses,
    AddClass,
    AddClassField,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class FileDraftMetadataPreset(Preset):
    """Preset for file metadata class."""

    provides = ("FileDraftMetadata",)

    depends_on = (
        # need to have this dependency because of __record_model_cls__ attribute
        "DraftMetadata",
    )

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass("FileDraftMetadata")
        yield AddClassField(
            "FileDraftMetadata",
            "__tablename__",
            f"{builder.model.base_name}_draft_files",
        )
        yield AddClassField(
            "FileDraftMetadata",
            "__record_model_cls__",
            dependencies.get("DraftMetadata"),
        )
        yield AddBaseClasses("FileDraftMetadata", db.Model, RecordMetadataBase, FileRecordModelMixin)
