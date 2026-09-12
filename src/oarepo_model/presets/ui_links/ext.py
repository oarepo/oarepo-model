# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""UI presets for generating ui.json for Jinja components and JavaScript."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import (
    Customization,
    PrependMixin,
)
from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.ext import RecordExtensionProtocol

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class UILinksFeaturePreset(Preset):
    """Preset for enabling UI links feature."""

    modifies = ("Ext",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class UILinksFeatureMixin(RecordExtensionProtocol):
            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                try:
                    version = importlib.import_module("oarepo_ui").__version__
                except ImportError:
                    version = "unknown"

                parent_model_args = super().model_arguments
                return {
                    **parent_model_args,
                    "features": {
                        **parent_model_args["features"],
                        "ui-links": {"version": version},
                    },
                }

        yield PrependMixin("Ext", UILinksFeatureMixin)
