# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for adding media files support to published records.

This module provides a preset that extends published records with media files
functionality by adding system fields for managing media files, including
the media_files FilesField and associated bucket fields for file storage.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.services.records.components.media_files import (
    MediaFilesAttrConfig,
)
from invenio_records.systemfields import ModelField
from invenio_records_resources.records.systemfields import (
    FilesField,
)

from oarepo_model.customizations import (
    Customization,
    PrependMixin,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordWithMediaFilesPreset(Preset):
    """Preset that adds media files support to published records."""

    depends_on = (
        "MediaFileRecord",  # need to have this dependency because of system fields
    )
    modifies = ("Record",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class RecordWithMediaFilesMixin:
            media_files = FilesField(
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
            media_bucket_id = ModelField(dump=False)
            media_bucket = ModelField(dump=False)

        yield PrependMixin(
            "Record",
            RecordWithMediaFilesMixin,
        )
