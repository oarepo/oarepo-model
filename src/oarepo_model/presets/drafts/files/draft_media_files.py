#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for adding media files support to draft records.

This module provides the DraftMediaFilesPreset that adds
media file handling capabilities to draft record models.
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


class DraftMediaFilesPreset(Preset):
    """Preset for adding media files support to draft records."""

    depends_on = ("Draft", "MediaFileDraft")

    provides = ("DraftMediaFiles",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class DraftMediaFilesMixin:
            files = FilesField(
                key=MediaFilesAttrConfig["_files_attr_key"],
                bucket_id_attr=MediaFilesAttrConfig["_files_bucket_id_attr_key"],
                bucket_attr=MediaFilesAttrConfig["_files_bucket_attr_key"],
                store=False,
                dump=False,
                file_cls=dependencies["MediaFileDraft"],
                # Don't delete, we'll manage in the service
                delete=False,
            )

        yield AddClass(
            "DraftMediaFiles",
            clazz=dependencies["Draft"],
        )
        yield PrependMixin(
            "DraftMediaFiles",
            DraftMediaFilesMixin,
        )
