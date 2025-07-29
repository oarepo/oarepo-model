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

from invenio_drafts_resources.services.records.components.media_files import (
    MediaFilesAttrConfig,
)
from invenio_records_resources.records.systemfields import FilesField

from oarepo_model.customizations import (
    AddClass,
    AddMixins,
    Customization,
)
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class DraftMediaFilesPreset(Preset):
    """
    Preset for records_resources.records
    """

    depends_on = ["Draft", "MediaFileDraft"]

    provides = [
        "DraftMediaFiles",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
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
        yield AddMixins(
            "DraftMediaFiles",
            DraftMediaFilesMixin,
        )
