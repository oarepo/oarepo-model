#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset that registers the geo search parameter interpreters."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import AddParamInterpreterCls, Customization
from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.services.records.params.spherical import (
    GeoBoundingBoxParam,
    GeoDistanceParam,
    GeoShapeParam,
    IcrsBoundingBoxParam,
    IcrsDistanceParam,
    IcrsShapeParam,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class GeoPreset(Preset):
    """Preset that registers the geo search parameter interpreters."""

    modifies = ("extra_param_interpreter_classes",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddParamInterpreterCls(GeoDistanceParam)
        yield AddParamInterpreterCls(GeoBoundingBoxParam)
        yield AddParamInterpreterCls(GeoShapeParam)
        yield AddParamInterpreterCls(IcrsDistanceParam)
        yield AddParamInterpreterCls(IcrsBoundingBoxParam)
        yield AddParamInterpreterCls(IcrsShapeParam)
