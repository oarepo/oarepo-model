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

from invenio_records_resources.records.api import FileRecord as InvenioFileRecord

from oarepo_model.customizations import (
    AddClass,
    AddMixins,
    Customization,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class MediaFileDraftPreset(Preset):
    """
    Preset for records_resources.records
    """

    provides = [
        "MediaFileDraft",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        class FileRecordMixin:
            """Mixin for the file record."""

            model_cls = Dependency("MediaFileDraftMetadata")
            record_cls = Dependency("DraftMediaFiles")

        yield AddClass(
            "MediaFileDraft",
            clazz=InvenioFileRecord,
        )
        yield AddMixins(
            "MediaFileDraft",
            FileRecordMixin,
        )
