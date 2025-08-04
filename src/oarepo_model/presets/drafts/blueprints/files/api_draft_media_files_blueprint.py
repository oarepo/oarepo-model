#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""API blueprint preset for draft media file operations.

This module provides the ApiDraftMediaFilesBlueprintPreset that configures
API blueprints for handling draft media file operations in Invenio applications.
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


class ApiDraftMediaFilesBlueprintPreset(Preset):
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
        @staticmethod  # type: ignore[misc]
        def create_draft_media_files_api_blueprint(app: Flask) -> Blueprint:
            with app.app_context():
                return app.extensions[model.base_name].draft_media_files_resource.as_blueprint()

        yield AddToModule(
            "blueprints",
            "create_draft_media_files_api_blueprint",
            create_draft_media_files_api_blueprint,
        )

        yield AddEntryPoint(
            group="invenio_base.api_blueprints",
            name=f"{model.base_name}_draft_media_files",
            value="blueprints:create_draft_media_files_api_blueprint",
            separator=".",
        )
