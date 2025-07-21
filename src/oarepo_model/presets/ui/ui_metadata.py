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

from oarepo_model.customizations import AddToDictionary, Customization
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

from .ui_record import get_ui_model

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class UIMetadataPreset(Preset):
    """
    Preset generating UI schema for Jinja components and javascript.
    """

    modifies = [
        "ui_model",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        if model.metadata_type:
            metadata_ui_model = get_ui_model(builder, model.metadata_type, ["metadata"])

            yield AddToDictionary(
                "ui_model", {"children": {"metadata": metadata_ui_model}}, patch=True
            )
