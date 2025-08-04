#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for creating media file draft API class.

This module provides a preset that creates a MediaFileDraft class based on
Invenio's FileRecord API. This class represents individual media files
attached to draft records during the editing process and provides methods
for media file manipulation and metadata access.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.records.api import FileRecord as InvenioFileRecord

from oarepo_model.customizations import (
    AddClass,
    AddMixins,
    Customization,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder


class MediaFileDraftPreset(Preset):
    """Preset that creates a MediaFileDraft class."""

    provides = ("MediaFileDraft",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
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
