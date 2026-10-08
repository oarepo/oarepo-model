# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to generate record schema mixin with media files metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

import marshmallow as ma
from invenio_rdm_records.services.schemas.files import FilesSchema
from marshmallow_utils.fields import (
    NestedAttribute,
)

from oarepo_model.customizations import Customization, PrependMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordWithMediaFilesSchemaPreset(Preset):
    """Preset for record service class.

    Without this, ``media_files.enabled`` is never present in the data a request handler
    sees (the schema silently drops it as unknown), so ``DraftMediaFilesComponent.create``
    always falls back to its disabled default and a draft's media files can never be
    switched on through the API - mirrors ``RecordWithFilesSchemaPreset``.
    """

    modifies = ("RecordSchema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:

        class RecordWithMediaFilesMixin(ma.Schema):
            media_files = NestedAttribute(FilesSchema)

        yield PrependMixin("RecordSchema", RecordWithMediaFilesMixin)
