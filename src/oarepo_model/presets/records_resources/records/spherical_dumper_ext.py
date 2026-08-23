#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Spherical coordinate dumper extensions generated from model data types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import AddToList, Customization
from oarepo_model.datatypes.spherical import ICRSDataType
from oarepo_model.datatypes.tree import get_model_nodes
from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.records.path_dumper_ext import PathDumperExtBase

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class ICRSDumperExt(PathDumperExtBase):
    """Dump ICRS into geo_point fields."""

    def _data_to_opensearch(self, data: dict[str, Any], key: str) -> None:
        """Convert a icrs field to geo_point field."""
        alpha = data[key]["ra"]
        delta = data[key]["dec"]
        data[key] = {
            "lat": delta,
            "lon": ((alpha + 180) % 360) - 180,
        }

    def _data_from_opensearch(self, data: dict[str, Any], key: str) -> None:
        """Convert a geo_point field to a icrs field."""
        lat = data[key]["lat"]
        lon = data[key]["lon"]
        data[key] = {
            "ra": lon % 360,
            "dec": lat,
        }


class ICRSDumperExtPreset(Preset):
    """Preset that converts icrs fields to geo_point opensearch fields and vice versa."""

    modifies = ("record_dumper_extensions",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        paths = [
            path
            for _datatype, path in get_model_nodes(
                builder,
                model,
                lambda datatype: isinstance(datatype, ICRSDataType),
                unique=True,
            )
        ]

        if paths:
            yield AddToList("record_dumper_extensions", ICRSDumperExt(paths))
