#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from oarepo_model.customizations import (
    AddEntryPoint,
    AddModule,
    AddToModule,
    Customization,
)
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class ApiFilesBlueprintPreset(Preset):
    """
    Preset for api blueprint.
    """

    provides = ["blueprints"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        yield AddModule("blueprints", exists_ok=True)

        @staticmethod  # need to use staticmethod as python's magic always passes self as the first argument
        def create_files_api_blueprint(app):
            """Create FilesRecord blueprint."""
            with app.app_context():
                blueprint = app.extensions[
                    model.base_name
                ].files_resource.as_blueprint()

            return blueprint

        yield AddToModule(
            "blueprints", "create_files_api_blueprint", create_files_api_blueprint
        )

        yield AddEntryPoint(
            group="invenio_base.api_blueprints",
            name=f"{model.base_name}_files",
            value="blueprints:create_files_api_blueprint",
            separator=".",
        )
