# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for creating draft file service.

This module provides a preset that creates a DraftFileService class based on
the Invenio FileService. This service handles operations on regular files
attached to draft records, including upload, download, and management operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.services.files import FileService

from oarepo_model.customizations import (
    AddClass,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftFileServicePreset(Preset):
    """Preset for file service class."""

    provides = ("DraftFileService",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass("DraftFileService", clazz=FileService)
