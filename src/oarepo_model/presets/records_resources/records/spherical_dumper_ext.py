# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Spherical coordinate dumper extensions generated from model data types."""

from __future__ import annotations

from typing import Any

from oarepo_model.datatypes.spherical import ICRSDataType
from oarepo_model.presets.records_resources.records.path_dumper_ext import (
    PathDumperExtBase,
    PathDumperExtPreset,
)


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


class ICRSDumperExtPreset(PathDumperExtPreset):
    """Preset that converts icrs fields to geo_point opensearch fields and vice versa."""

    datatype_class = ICRSDataType
    dumper_ext_class = ICRSDumperExt
