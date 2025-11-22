#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for creating record media files API class.

This module provides a preset that creates a RecordMediaFiles class that
extends the base Record class with media files functionality. This class
provides an interface for managing media files attached to published records.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.services.records.components.media_files import (
    MediaFilesAttrConfig,
)
from invenio_records_resources.records.systemfields import FilesField

from oarepo_model.customizations import (
    AddClass,
    Customization,
    PrependMixin,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordMediaFilesPreset(Preset):
    """Preset that creates RecordMediaFiles class."""

    depends_on = ("Record", "MediaFileRecord")

    provides = ("RecordMediaFiles",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class RecordMediaFilesMixin:
            files = FilesField(
                key=MediaFilesAttrConfig["_files_attr_key"],
                bucket_id_attr=MediaFilesAttrConfig["_files_bucket_id_attr_key"],
                bucket_attr=MediaFilesAttrConfig["_files_bucket_attr_key"],
                store=False,
                dump=False,
                file_cls=dependencies["MediaFileRecord"],
                # Don't create
                create=False,
                # Don't delete, we'll manage in the service
                delete=False,
            )

        yield AddClass(
            "RecordMediaFiles",
            clazz=dependencies["Record"],
        )
        yield PrependMixin(
            "RecordMediaFiles",
            RecordMediaFilesMixin,
        )
