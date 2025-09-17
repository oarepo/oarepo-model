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

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources import __version__

from oarepo_model.customizations import (
    AddMixins,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class UIFeaturePreset(Preset):
    """Preset for enabling UI feature."""

    modifies = ("Ext",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class UIFeatureMixin:
            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                parent_model_args = super().model_arguments  # type: ignore[misc] # pyright: ignore[reportAttributeAccessIssue]
                return {
                    **parent_model_args,
                    "features": {**parent_model_args["features"], "ui": {"version": __version__}},
                }

        yield AddMixins("Ext", UIFeatureMixin)
