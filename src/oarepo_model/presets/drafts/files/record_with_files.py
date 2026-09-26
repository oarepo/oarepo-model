# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for modifying file support to published records when drafts are used.

This module provides the RecordWithFilesPreset that modifies
file handling capabilities to published record models when drafts are used.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

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


class RecordWithFilesPreset(Preset):
    """Preset for adding file support to published records."""

    depends_on = (
        "FileRecord",  # need to have this dependency because of system fields
    )
    modifies = ("Record",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class RecordWithFilesMixin:
            files = FilesField(
                store=False,
                create=False,
                delete=False,
                file_cls=dependencies.get("FileRecord"),
            )

        yield PrependMixin(
            "Record",
            RecordWithFilesMixin,
        )
