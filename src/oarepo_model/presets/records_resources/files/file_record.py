# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for creating FileRecord API class.

This module provides a preset that creates a FileRecord class based on
Invenio's FileRecord API. The FileRecord represents individual files
attached to records and provides methods for file manipulation and metadata access.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.records.api import FileRecord as InvenioFileRecord

from oarepo_model.customizations import (
    AddClass,
    Customization,
    PrependMixin,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder


class FileRecordPreset(Preset):
    """Preset for FileRecord class."""

    provides = ("FileRecord",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class FileRecordMixin:
            """Mixin for the file record."""

            model_cls = Dependency("FileMetadata")
            record_cls = Dependency("Record")

        yield AddClass(
            "FileRecord",
            clazz=InvenioFileRecord,
        )
        yield PrependMixin(
            "FileRecord",
            FileRecordMixin,
        )
