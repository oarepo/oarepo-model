#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""API blueprint preset for record operations.

This module provides the ApiBlueprintPreset that configures
API blueprints for handling record operations in Invenio applications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import (
    AddDictionary,
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


class ApiBlueprintPreset(Preset):
    """Preset for api blueprint."""

    modifies = ("blueprints",)
    provides = ("api_application_blueprint_initializers",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddDictionary("api_application_blueprint_initializers", exists_ok=True)

        runtime_dependencies = builder.get_runtime_dependencies()

        @staticmethod  # need to use staticmethod as python's magic always passes self as the first argument
        def create_api_blueprint(app: Flask) -> Blueprint:
            """Create DocumentsRecord blueprint."""
            with app.app_context():
                blueprint = app.extensions[model.base_name].records_resource.as_blueprint()

                for initializer_func in runtime_dependencies.get(
                    "api_application_blueprint_initializers",
                ).values():
                    blueprint.record_once(initializer_func)

            return blueprint

        yield AddToModule("blueprints", "create_api_blueprint", create_api_blueprint)

        yield AddEntryPoint(
            group="invenio_base.api_blueprints",
            name=model.base_name,
            value="blueprints:create_api_blueprint",
            separator=".",
        )
