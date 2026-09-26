# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for configuring draft media file resource.

This module provides a preset that creates and configures a DraftMediaFileResourceConfig
for draft media file REST API endpoints. It sets up the blueprint name and URL prefix
for accessing media files on draft records.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.resources import FileResourceConfig

from oarepo_model.customizations import (
    AddClass,
    Customization,
    PrependMixin,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset
from oarepo_model.presets.drafts.resources.files.media_file_resource_config import (
    MEDIA_FILE_ROUTES,
)

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping

    from oarepo_model.builder import InvenioModelBuilder


class DraftMediaFileResourceConfigPreset(Preset):
    """Preset for file resource config class."""

    provides = ("DraftMediaFileResourceConfig",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class DraftMediaFileResourceConfigMixin:
            blueprint_name = f"{model.base_name}_draft_media_files"
            url_prefix = f"/{model.slug}/<pid_value>/draft"
            # media files live under '/media-files', not the plain '/files' inherited from
            # FileResourceConfig - see media_file_resource_config.MEDIA_FILE_ROUTES.
            routes: Mapping[str, str] = MEDIA_FILE_ROUTES
            # Response handling
            response_handlers = Dependency("media_file_response_handlers")

        yield AddClass("DraftMediaFileResourceConfig", clazz=FileResourceConfig)
        yield PrependMixin(
            "DraftMediaFileResourceConfig",
            DraftMediaFileResourceConfigMixin,
        )
