# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Unit tests for geo_point/geo_shape/icrs/icrs_shape data types."""

from __future__ import annotations

from typing import Any

import marshmallow as ma
import pytest


def _schema(datatype_registry, element: dict[str, Any]) -> ma.Schema:
    fld = datatype_registry.get_type(element).create_marshmallow_field(field_name="a", element=element)
    return ma.Schema.from_dict({"a": fld})()


class TestGeoPointFacets:
    """Geo fields must not generate search facets.

    A geo_point mapping has no lat/lon (or ra/dec) sub-fields, so a terms
    facet on them could never return data - no facets may be generated.
    """

    @pytest.mark.parametrize("type_name", ["geo_point", "geo_shape", "icrs", "icrs_shape"])
    def test_geo_types_produce_no_facets(self, datatype_registry, type_name):
        """Create no facet entries for geo fields."""
        dt = datatype_registry.get_type({"type": type_name})
        facets = dt.get_facet("metadata.point", {"type": type_name}, [], {})
        assert facets == {}


def _reject_all(value: Any) -> None:
    raise ma.ValidationError("rejected by marshmallow_validate")


class TestGeoShapeValidation:
    """geo_shape gets its validate_geo_shape *in addition* to user validators."""

    @pytest.mark.parametrize("type_name", ["geo_shape", "icrs_shape"])
    def test_marshmallow_validate_is_not_overwritten(self, datatype_registry, type_name):
        """Keep the user's marshmallow_validate validators next to the shape validator."""
        schema = _schema(
            datatype_registry,
            {
                "type": type_name,
                "marshmallow_validate": [f"{__name__}._reject_all"],
            },
        )
        with pytest.raises(ma.ValidationError, match="rejected by marshmallow_validate"):
            schema.load({"a": "POINT (14.5 50.0)"})

    @pytest.mark.parametrize("type_name", ["geo_shape", "icrs_shape"])
    def test_shape_validator_still_runs(self, datatype_registry, type_name):
        """Validate the geo shape itself even with marshmallow_validate present."""
        schema = _schema(datatype_registry, {"type": type_name})
        assert schema.load({"a": "POINT (14.5 50.0)"}) == {"a": "POINT (14.5 50.0)"}
        with pytest.raises(ma.ValidationError):
            schema.load({"a": "not a shape"})
