# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for creating media file service.

This module provides a preset that creates a MediaFileService class based on
the Invenio FileService. This service handles operations on media files
attached to published records.
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


class MediaFileServicePreset(Preset):
    """Preset for file service class."""

    provides = ("MediaFileService",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass("MediaFileService", clazz=FileService)
