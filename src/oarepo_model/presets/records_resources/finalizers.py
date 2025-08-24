#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for adding finalization tasks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import (
    AddEntryPoint,
    AddList,
    AddModule,
    AddToModule,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask import Flask

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class FinalizationPreset(Preset):
    """Preset for adding finalization tasks.

    This preset provides a list of api_finalizers and app_finalizers that are
    called during the finalization phase of the model.
    """

    provides = ("api_finalizers", "app_finalizers")

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddModule("finalizers", exists_ok=True)
        yield AddList("api_finalizers")
        yield AddList("app_finalizers")

        runtime_dependencies = builder.get_runtime_dependencies()

        @staticmethod  # type: ignore[misc]
        def api_finalizer(app: Flask) -> None:
            for finalizer_func in runtime_dependencies.get("api_finalizers"):
                finalizer_func(app)

        @staticmethod  # type: ignore[misc]
        def app_finalizer(app: Flask) -> None:
            for finalizer_func in runtime_dependencies.get("app_finalizers"):
                finalizer_func(app)

        yield AddToModule("finalizers", "api_finalizer", api_finalizer)
        yield AddToModule("finalizers", "app_finalizer", app_finalizer)

        yield AddEntryPoint(
            group="invenio_base.finalize_app",
            name=model.base_name,
            value="finalizers:app_finalizer",
            separator=".",
        )
        yield AddEntryPoint(
            group="invenio_base.api_finalize_app",
            name=model.base_name,
            value="finalizers:api_finalizer",
            separator=".",
        )
