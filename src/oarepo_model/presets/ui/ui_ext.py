#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Extension preset for UI.json registration.

This module provides the ExtUIPreset that registers ui.json
to oarepo_runtime's Model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import (
    Customization,
    PrependMixin,
)
from oarepo_model.model import InvenioModel, ModelMixin
from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.ext import RecordExtensionProtocol

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask import Flask

    from oarepo_model.builder import InvenioModelBuilder


class UIExtPreset(Preset):
    """Preset for extension class."""

    modifies = ("Ext",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class ExtUIMixin(ModelMixin, RecordExtensionProtocol):
            """Mixin for extension class."""

            app: Flask

            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                return {
                    **super().model_arguments,
                    "ui_model": builder.runtime_dependencies.get("ui_model"),
                    "ui_blueprint_name": f"{model.configuration.get('ui_blueprint_name')}",
                }

        yield PrependMixin("Ext", ExtUIMixin)
