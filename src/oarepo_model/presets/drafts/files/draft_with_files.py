# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for adding file support to draft records.

This module provides the DraftWithFilesPreset that adds
file handling capabilities to draft record models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

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


class DraftWithFilesPreset(Preset):
    """Preset that adds file support to draft records."""

    depends_on = ("FileDraft",)  # need to have this dependency because of system fields
    modifies = ("Draft",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class DraftWithFilesMixin:
            files = FilesField(
                store=False,
                file_cls=dependencies["FileDraft"],
                dump=False,
                # Don't delete, we'll manage in the service
                delete=False,
            )
            bucket_id = ModelField(dump=False)
            bucket = ModelField(dump=False)

        yield PrependMixin(
            "Draft",
            DraftWithFilesMixin,
        )
