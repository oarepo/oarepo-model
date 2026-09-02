#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Data type for geo fields."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

import marshmallow
from marshmallow.exceptions import ValidationError
from shapely import wkt as shapely_wkt
from shapely.errors import ShapelyError
from shapely.geometry import shape as shapely_shape
from shapely.ops import transform as shapely_transform

from oarepo_model.datatypes.collections import ObjectDataType

if TYPE_CHECKING:
    from shapely.geometry.base import BaseGeometry

#: GeoJSON geometry types an OpenSearch ``geo_shape`` field accepts (matched
#: case-insensitively). Excludes OpenSearch's non-GeoJSON ``envelope`` type,
#: which shapely cannot represent.
#: https://docs.opensearch.org/latest/mappings/supported-field-types/geo-shape/
_OPENSEARCH_GEOMETRY_TYPES = frozenset(
    {
        "point",
        "multipoint",
        "linestring",
        "multilinestring",
        "polygon",
        "multipolygon",
        "geometrycollection",
    }
)


def validate_geo_shape(value: Any) -> None:
    """Validate a geo shape: either a WKT string or a GeoJSON geometry object."""
    if value is None:
        return

    try:
        if isinstance(value, str):
            shapely_wkt.loads(value)
            return
        if isinstance(value, dict) and str(value.get("type", "")).lower() in _OPENSEARCH_GEOMETRY_TYPES:
            shapely_shape(value)
            return
    except (ShapelyError, NotImplementedError, TypeError, ValueError, KeyError) as error:
        # NotImplementedError comes from shapely's unimplemented curved geometries.
        raise ValidationError(f"Invalid geo shape: {error}") from error

    raise ValidationError("Geo shape must be a WKT string or a GeoJSON geometry object.")


def ra_dec_to_lat_lon(ra: float, dec: float) -> tuple[float, float]:
    """Convert ICRS right ascension/declination (degrees) to geo lat/lon.

    Right ascension is folded from [0, 360) to the [-180, 180] range OpenSearch's
    geo fields require; declination is already a latitude.
    """
    return dec, ((ra + 180) % 360) - 180


def lat_lon_to_ra_dec(lat: float, lon: float) -> tuple[float, float]:
    """Convert geo lat/lon back to ICRS right ascension/declination (degrees)."""
    return lon % 360, lat


def icrs_shape_to_lon_lat(geometry: BaseGeometry) -> BaseGeometry:
    """Rewrite a geometry's (ra, dec) coordinates as geo (lon, lat).

    A third (height) ordinate, if present, is dropped: OpenSearch's geo_shape
    field is two-dimensional.
    """

    def _transform(ra: float, dec: float, *_: float) -> tuple[float, float]:
        lat, lon = ra_dec_to_lat_lon(ra, dec)
        return lon, lat

    return shapely_transform(_transform, geometry)


def lon_lat_to_icrs_shape(geometry: BaseGeometry) -> BaseGeometry:
    """Rewrite a geometry's geo (lon, lat) coordinates as ICRS (ra, dec)."""

    def _transform(lon: float, lat: float, *_: float) -> tuple[float, float]:
        ra, dec = lat_lon_to_ra_dec(lat, lon)
        return ra, dec

    return shapely_transform(_transform, geometry)


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


class GeoShapeDataType(ObjectDataType):
    """Data type for geo shapes.

    A geo shape is a single GeoJSON shape or a WKT string.
    Geometry collections are supported.
    """

    mapping_type = "geo_shape"
    TYPE = "geo_shape"

    #: The shape is stored as given, either WKT or GeoJSON, so nothing is transformed.
    marshmallow_field_class = marshmallow.fields.Raw

    @override
    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        """Get the properties for the geo shape data type."""
        return {}

    @override
    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        """Add the shapely validator and drop 'nested', which Raw does not accept."""
        args = super()._get_marshmallow_field_args(field_name, element)
        args.pop("nested", None)
        args["validate"] = validate_geo_shape
        return args

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        """No UI-specific rendering: without this, the inherited empty nested schema would dump the shape as ``{}``."""
        return {}

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create the mapping for the geo shape data type.

        ``coerce``: closes unclosed rings, which ``validate_geo_shape`` already
        accepts (shapely closes them silently too). ``ignore_malformed``: shapely's
        WKT/GeoJSON grammar and OpenSearch's geometry parser disagree on some inputs
        (empty geometries, WKT Z/M/ZM, self-intersecting polygons); a shape that
        validates here but chokes OpenSearch is skipped from the geo index rather
        than failing the whole document, and stays in ``_source`` unchanged.
        ``doc_values``: OpenSearch's geo_shape doc values hold only one value per
        document, so without disabling them an array of shapes fails to index
        entirely ("DocValuesField ... appears more than once"). Not needed here
        since geo_shape queries use the indexed shape tree, not doc values.
        """
        return {
            "type": self.mapping_type,
            "coerce": True,
            "ignore_malformed": True,
            "doc_values": False,
        }

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create the JSON schema for the geo shape data type.

        Either a WKT string or a GeoJSON object; the GeoJSON structure is
        intentionally not validated here.
        """
        return {"type": ["string", "object"]}


class ICRSShapeDataType(GeoShapeDataType):
    """Data type for ICRS shapes.

    Like a geo shape, but the WKT/GeoJSON x/y coordinates are read as ICRS
    right ascension/declination (degrees) rather than lon/lat. The mapping stays
    ``geo_shape``, so :class:`ICRSShapeDumperExt` converts the coordinates when
    the shape is indexed.

    See https://aa.usno.navy.mil/faq/ICRS_doc for more information.
    """

    TYPE = "icrs_shape"


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
