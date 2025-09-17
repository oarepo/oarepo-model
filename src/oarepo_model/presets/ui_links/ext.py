#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""UI presets for generating ui.json for Jinja components and JavaScript."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import (
    AddMixins,
    Customization,
)
from oarepo_model.presets import Preset

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
        class UILinksFeatureMixin:
            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                try:
                    version = importlib.import_module("oarepo_ui").__version__
                except ImportError:
                    version = "unknown"

                parent_model_args = super().model_arguments  # type: ignore[misc] # pyright: ignore[reportAttributeAccessIssue]
                return {
                    **parent_model_args,
                    "features": {**parent_model_args["features"], "ui-links": {"version": version}},
                }

        yield AddMixins("Ext", UILinksFeatureMixin)
