# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Data type for geo fields."""

from __future__ import annotations

from typing import Any, override

from oarepo_model.datatypes.collections import ObjectDataType


class GeoPointDataType(ObjectDataType):
    """Data type for geo points (latitude/longitude)."""

    mapping_type = "geo_point"
    TYPE = "geo_point"

    @override
    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        """Get the properties for the geo point data type."""
        return {
            "lat": {"type": "double"},
            "lon": {"type": "double"},
        }

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create the mapping for the geo point data type."""
        return {
            "type": self.mapping_type,
        }


class ICRSDataType(GeoPointDataType):
    """Data type for ICRS coordinates.

    See https://aa.usno.navy.mil/faq/ICRS_doc for more information.
    """

    mapping_type = "geo_point"
    TYPE = "icrs"

    @override
    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        """Get the properties for the ICRS data type."""
        return {
            "ra": {"type": "double"},
            "dec": {"type": "double"},
        }

    # note: mapping type is set to "geo_point" by default, we need to convert the ra/dec to lat/lon
    # in a specialized dumper if we want to use this data type
