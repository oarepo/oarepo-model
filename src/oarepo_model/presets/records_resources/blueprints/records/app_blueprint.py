#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Application blueprint preset for record operations.

This module provides the AppBlueprintPreset that configures
application-level blueprints for handling record views and UI in Invenio applications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from flask import Blueprint

from oarepo_model.customizations import (
    AddDictionary,
    AddEntryPoint,
    AddToModule,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask import Flask

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AppBlueprintPreset(Preset):
    """Preset for app blueprint."""

    modifies = ("blueprints",)
    provides = ("app_application_blueprint_initializers",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddDictionary("app_application_blueprint_initializers", exists_ok=True)

        runtime_dependencies = builder.get_runtime_dependencies()

        # need to use staticmethod as python's magic always passes self as the first argument
        @staticmethod  # type: ignore[misc]
        def create_app_blueprint(app: Flask) -> Blueprint:
            """Create DocumentsRecord blueprint."""
            with app.app_context():
                blueprint = Blueprint(
                    f"{model.base_name}_app",
                    __name__,
                    url_prefix="/{model.slug}/",
                )

                for initializer_func in cast(
                    "dict",
                    runtime_dependencies.get("app_application_blueprint_initializers"),
                ).values():
                    blueprint.record_once(initializer_func)

            return blueprint

        yield AddToModule("blueprints", "create_app_blueprint", create_app_blueprint)

        yield AddEntryPoint(
            group="invenio_base.blueprints",
            name=model.base_name,
            value="blueprints:create_app_blueprint",
            separator=".",
        )
