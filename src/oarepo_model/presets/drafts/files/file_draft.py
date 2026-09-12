# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for draft file record model.

This module provides the FileDraftPreset that creates
draft file record API classes for handling file operations.
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


class FileDraftPreset(Preset):
    """Preset that creates a FileDraft class."""

    provides = ("FileDraft",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class FileRecordMixin:
            """Mixin for the file record."""

            model_cls = Dependency("FileDraftMetadata")
            record_cls = Dependency("Draft")

        yield AddClass(
            "FileDraft",
            clazz=InvenioFileRecord,
        )
        yield PrependMixin(
            "FileDraft",
            FileRecordMixin,
        )
