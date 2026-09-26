# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""API blueprint preset for media file operations.

This module provides the ApiMediaFilesBlueprintPreset that configures
API blueprints for handling published record media file operations in Invenio applications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import (
    AddEntryPoint,
    AddToModule,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask import Blueprint, Flask

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class ApiMediaFilesBlueprintPreset(Preset):
    """Preset for api blueprint."""

    modifies = ("blueprints",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        # need to use staticmethod as python's magic always passes self as the first argument
        def create_media_files_api_blueprint(app: Flask) -> Blueprint:
            with app.app_context():
                return app.extensions[model.base_name].media_files_resource.as_blueprint()

        yield AddToModule(
            "blueprints",
            "create_media_files_api_blueprint",
            staticmethod(create_media_files_api_blueprint),
        )

        yield AddEntryPoint(
            group="invenio_base.api_blueprints",
            name=f"{model.base_name}_media_files",
            value="blueprints:create_media_files_api_blueprint",
            separator=".",
        )
