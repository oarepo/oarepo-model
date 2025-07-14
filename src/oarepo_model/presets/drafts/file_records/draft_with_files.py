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

from invenio_records.systemfields import ModelField
from invenio_records_resources.records.systemfields import (
    FilesField,
)

from oarepo_model.customizations import (
    AddMixins,
    Customization,
)
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class DraftWithFilesPreset(Preset):
    """
    Preset for records_resources.records
    """

    depends_on = [
        "FileDraft",  # need to have this dependency because of system fields
    ]
    modifies = ["Draft"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        class DraftWithFilesMixin:

            files = FilesField(
                store=False,
                file_cls=dependencies["FileDraft"],
                dump=False,
                # Don't delete, we'll manage in the service
                delete=False,
            )
            bucket_id = ModelField()
            bucket = ModelField(dump=False)

        yield AddMixins(
            "Draft",
            DraftWithFilesMixin,
        )
