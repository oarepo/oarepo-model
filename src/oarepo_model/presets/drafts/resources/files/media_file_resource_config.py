# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for configuring media file resource.

This module provides a preset that creates and configures a MediaFileResourceConfig
for media file REST API endpoints. It sets up the blueprint name and URL prefix
for accessing media files on published records.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.resources import FileResourceConfig

from oarepo_model.customizations import (
    AddClass,
    AddDictionary,
    Customization,
    PrependMixin,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping

    from oarepo_model.builder import InvenioModelBuilder

#: mirrors upstream's invenio_rdm_records media routes: media files live under '/media-files',
#: not the plain '/files' inherited from FileResourceConfig - the two would otherwise register
#: identical rules and the plain-file blueprint would silently win every match
MEDIA_FILE_ROUTES: Mapping[str, str] = {
    "list": "/media-files",
    "item": "/media-files/<path:key>",
    "item-content": "/media-files/<path:key>/content",
    "item-multipart-content": "/media-files/<path:key>/content/<int:part>",
    "item-commit": "/media-files/<path:key>/commit",
    "list-archive": "/media-files-archive",
}


class MediaFileResourceConfigPreset(Preset):
    """Preset for file resource config class."""

    provides = ("MediaFileResourceConfig", "media_file_response_handlers")

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class MediaFileResourceConfigMixin:
            blueprint_name = f"{model.base_name}_media_files"
            url_prefix = f"/{model.slug}/<pid_value>"
            routes: Mapping[str, str] = MEDIA_FILE_ROUTES
            # Response handling
            response_handlers = Dependency("media_file_response_handlers")

        yield AddClass("MediaFileResourceConfig", clazz=FileResourceConfig)
        yield PrependMixin("MediaFileResourceConfig", MediaFileResourceConfigMixin)

        yield AddDictionary(
            "media_file_response_handlers",
            {**FileResourceConfig.response_handlers},
        )
