#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Search parameter interpreters for geo filtering."""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING, Any, ClassVar

from invenio_i18n import gettext as _
from invenio_records_resources.services.errors import QuerystringValidationError
from invenio_records_resources.services.records.params.base import ParamInterpreter
from opensearch_dsl import Q
from shapely import wkt as shapely_wkt
from shapely.errors import ShapelyError
from shapely.geometry import mapping as shapely_mapping
from shapely.ops import transform as shapely_transform

if TYPE_CHECKING:
    from opensearch_dsl.search import Search
    from shapely.geometry.base import BaseGeometry

#: Mean earth radius in kilometers, used to convert angular distances to km.
_EARTH_RADIUS_KM = 6371.0088


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute the great-circle distance between two points, in kilometers."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _format_km(value: float) -> str:
    """Format a kilometer distance for use as a distance_feature pivot."""
    rounded = round(value, 3)
    if rounded == int(rounded):
        rounded = int(rounded)
    return f"{rounded}km"


def _degrees_to_km(degrees: float) -> float:
    """Convert a great-circle angle to a distance, in kilometers.

    ICRSDumperExt indexes right ascension/declination as if they were
    lon/lat on Earth, so OpenSearch's geo_distance/geo_shape queries already
    compute great-circle *angles* between ICRS points correctly - they're
    just expressed as a surface distance using earth's radius. Converting a
    requested angle (in degrees) to kilometers with that same radius makes
    the geo_distance query select exactly that angle, regardless of what the
    "surface" it's nominally measuring actually represents.
    """
    return _EARTH_RADIUS_KM * math.radians(degrees)


def _ra_dec_to_lat_lon(ra: float, dec: float) -> tuple[float, float]:
    """Convert ICRS right ascension/declination (degrees) to lat/lon.

    Mirrors the conversion ICRSDumperExt applies when indexing an icrs field
    as geo_point, so queries against that field see the same coordinates
    that were actually indexed.
    """
    return dec, ((ra + 180) % 360) - 180


class _PrefixedGeoParam(ParamInterpreter):
    """Base class for search parameter interpreters keyed by a fixed prefix.

    A subclass sets ``prefix`` and implements ``_apply_value`` to turn one
    raw ``prefix<field>=<value>`` occurrence into a change on the search.
    """

    #: Prefix of the query string parameter, e.g. ``geo_distance:metadata.location``.
    prefix: ClassVar[str]

    def apply(
        self,
        identity: Any,  # noqa: ARG002 for override
        search: Search,
        params: dict[str, Any],
    ) -> Search:
        """Evaluate the parameters on the search."""
        search = self._apply_from_mapping(search, params)

        # The default SearchRequestArgsSchema only recognizes q/suggest/sort/
        # page/size; every other query-string key (including our prefixed ones)
        # is bucketed by its post_load "facets" hook into params["facets"] rather
        # than left at the top level of params. Since this interpreter may run
        # either directly (params built by hand, e.g. in tests) or as part of a
        # real request (params built by that schema), we have to look in both
        # places. Keys are popped from wherever they are found so a facets
        # interpreter running later doesn't see them.
        facets = params.get("facets")
        if facets:
            search = self._apply_from_mapping(search, facets)

        return search

    def _apply_from_mapping(self, search: Search, mapping: dict[str, Any]) -> Search:
        for key in list(mapping.keys()):
            if not key.startswith(self.prefix):
                continue

            field = key[len(self.prefix) :]
            values = mapping.pop(key)

            for value in values:
                search = self._apply_value(search, field, value)

        return search

    def _apply_value(self, search: Search, field: str, value: str) -> Search:
        raise NotImplementedError


#: Matches ``[lat,lon,distance]`` or ``lat,lon,distance``.
_DISTANCE_VALUE_RE = re.compile(
    r"^\[?\s*(?P<lat>[+-]?\d+(?:\.\d+)?)\s*,\s*(?P<lon>[+-]?\d+(?:\.\d+)?)\s*,\s*"
    r"(?P<distance>\d+(?:\.\d+)?\s*[a-zA-Z]+)\s*\]?$"
)

#: Matches a distance value such as ``50km`` or ``12.5mi``.
_DISTANCE_RE = re.compile(r"^\s*(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>[a-zA-Z]+)\s*$")


class GeoDistanceParam(_PrefixedGeoParam):
    """Evaluate ``geo_distance:<field>=[lat,lon,distance]`` query parameters.

    For every occurrence of this parameter, records within ``distance`` of
    ``(lat, lon)`` are kept (``geo_distance`` filter on ``field``), and
    records closer to the point are additionally boosted in relevance via a
    ``distance_feature`` query, with the pivot set to a tenth of the
    requested distance.
    """

    prefix: ClassVar[str] = "geo_distance:"

    #: Fraction of the requested distance used as the ``distance_feature`` pivot.
    pivot_divisor: ClassVar[int] = 10

    def _apply_value(self, search: Search, field: str, value: str) -> Search:
        lat, lon, distance = self._parse_value(field, value)

        search = search.filter(
            "geo_distance",
            distance=distance,
            **{field: {"lat": lat, "lon": lon}},
        )
        return search.query(
            "bool",
            should=[
                Q(
                    "distance_feature",
                    field=field,
                    origin={"lat": lat, "lon": lon},
                    pivot=self._pivot(distance),
                )
            ],
        )

    def _parse_value(self, field: str, value: str) -> tuple[float, float, str]:
        match = _DISTANCE_VALUE_RE.match(value.strip())
        if not match:
            raise QuerystringValidationError(
                _(
                    "Invalid value %(value)r for parameter '%(param)s%(field)s'. "
                    "Expected '[lat,lon,distance]', e.g. '[50.0,14.4,50km]'.",
                    value=value,
                    param=self.prefix,
                    field=field,
                )
            )
        return (
            float(match.group("lat")),
            float(match.group("lon")),
            match.group("distance").replace(" ", ""),
        )

    def _pivot(self, distance: str) -> str:
        match = _DISTANCE_RE.match(distance)
        assert match is not None  # noqa: S101 -- already validated by _parse_value
        pivot_value = round(float(match.group("value")) / self.pivot_divisor, 6)
        if pivot_value == int(pivot_value):
            pivot_value = int(pivot_value)
        return f"{pivot_value}{match.group('unit')}"


#: Matches ``[lat,lon,lat,lon]`` or ``lat,lon,lat,lon`` (two opposite corners).
_BOUNDING_BOX_VALUE_RE = re.compile(
    r"^\[?\s*(?P<lat1>[+-]?\d+(?:\.\d+)?)\s*,\s*(?P<lon1>[+-]?\d+(?:\.\d+)?)\s*,\s*"
    r"(?P<lat2>[+-]?\d+(?:\.\d+)?)\s*,\s*(?P<lon2>[+-]?\d+(?:\.\d+)?)\s*\]?$"
)


class GeoBoundingBoxParam(_PrefixedGeoParam):
    """Evaluate ``geo_bounding_box:<field>=[lat,lon,lat,lon]`` query parameters.

    The two points are opposite corners of the box, in any order. For every
    occurrence of this parameter, records inside the box are kept
    (``geo_bounding_box`` filter on ``field``), and records closer to the
    center of the box are additionally boosted in relevance via a
    ``distance_feature`` query, with the pivot set to half of the box's
    diagonal, converted from degrees to kilometers.
    """

    prefix: ClassVar[str] = "geo_bounding_box:"

    def _apply_value(self, search: Search, field: str, value: str) -> Search:
        lat1, lon1, lat2, lon2 = self._parse_value(field, value)

        top_left = {"lat": max(lat1, lat2), "lon": min(lon1, lon2)}
        bottom_right = {"lat": min(lat1, lat2), "lon": max(lon1, lon2)}
        center = {"lat": (lat1 + lat2) / 2, "lon": (lon1 + lon2) / 2}
        # The diagonal length is the same regardless of which pair of opposite
        # corners was supplied, so it can be computed directly from the input.
        half_diagonal_km = _haversine_km(lat1, lon1, lat2, lon2) / 2

        search = search.filter(
            "geo_bounding_box",
            **{field: {"top_left": top_left, "bottom_right": bottom_right}},
        )
        return search.query(
            "bool",
            should=[
                Q(
                    "distance_feature",
                    field=field,
                    origin=center,
                    pivot=_format_km(half_diagonal_km),
                )
            ],
        )

    def _parse_value(self, field: str, value: str) -> tuple[float, float, float, float]:
        match = _BOUNDING_BOX_VALUE_RE.match(value.strip())
        if not match:
            raise QuerystringValidationError(
                _(
                    "Invalid value %(value)r for parameter '%(param)s%(field)s'. "
                    "Expected '[lat,lon,lat,lon]', e.g. '[50.2,14.2,49.9,14.6]'.",
                    value=value,
                    param=self.prefix,
                    field=field,
                )
            )
        return (
            float(match.group("lat1")),
            float(match.group("lon1")),
            float(match.group("lat2")),
            float(match.group("lon2")),
        )


#: Relations accepted by the OpenSearch geo_shape query.
_GEO_SHAPE_OPERATIONS = frozenset({"INTERSECTS", "DISJOINT", "WITHIN", "CONTAINS"})
_DEFAULT_GEO_SHAPE_OPERATION = "INTERSECTS"

#: Splits an optional leading operation keyword from the rest of the value (the WKT).
_GEO_SHAPE_OP_RE = re.compile(r"^\s*(?P<op>[A-Za-z]+)\s+(?P<rest>.+)$", re.DOTALL)


class GeoShapeParam(_PrefixedGeoParam):
    """Evaluate ``geo_shape:<field>=[OP ]<WKT>`` query parameters.

    ``OP`` is one of ``INTERSECTS`` (the default), ``DISJOINT``, ``WITHIN`` or
    ``CONTAINS`` and becomes the ``relation`` of a ``geo_shape`` filter on
    ``field``. The WKT geometry (e.g. ``POLYGON ((...))``) is parsed and
    converted to GeoJSON with shapely, since that's the format OpenSearch's
    geo_shape query expects for the ``shape`` value.
    """

    prefix: ClassVar[str] = "geo_shape:"

    def _apply_value(self, search: Search, field: str, value: str) -> Search:
        operation, shape = self._parse_value(field, value)

        return search.filter(
            "geo_shape",
            **{field: {"shape": shape, "relation": operation.lower()}},
        )

    def _parse_value(self, field: str, value: str) -> tuple[str, dict[str, Any]]:
        value = value.strip()
        operation = _DEFAULT_GEO_SHAPE_OPERATION
        wkt_text = value

        match = _GEO_SHAPE_OP_RE.match(value)
        if match and match.group("op").upper() in _GEO_SHAPE_OPERATIONS:
            operation = match.group("op").upper()
            wkt_text = match.group("rest")

        return operation, shapely_mapping(self._load_geometry(field, wkt_text))

    def _load_geometry(self, field: str, wkt_text: str) -> BaseGeometry:
        try:
            return shapely_wkt.loads(wkt_text)
        except ShapelyError as error:
            raise QuerystringValidationError(
                _(
                    "Invalid value %(value)r for parameter '%(param)s%(field)s'. "
                    "Expected '[OP ]<WKT>', e.g. 'WITHIN POLYGON ((0 0, 1 0, 1 1, 0 0))'.",
                    value=wkt_text,
                    param=self.prefix,
                    field=field,
                )
            ) from error


#: Matches ``[ra,dec,distance]`` or ``ra,dec,distance`` (distance in degrees, no unit).
_ICRS_DISTANCE_VALUE_RE = re.compile(
    r"^\[?\s*(?P<ra>[+-]?\d+(?:\.\d+)?)\s*,\s*(?P<dec>[+-]?\d+(?:\.\d+)?)\s*,\s*"
    r"(?P<distance>\d+(?:\.\d+)?)\s*\]?$"
)


class IcrsDistanceParam(GeoDistanceParam):
    """Evaluate ``icsr_distance:<field>=[ra,dec,distance]`` query parameters.

    ``ra``/``dec`` are ICRS right ascension/declination in degrees and
    ``distance`` is a great-circle angle, also in degrees (no unit suffix,
    unlike geo_distance:). Both are converted - ra/dec to lat/lon, distance
    to kilometers via :func:`_degrees_to_km` - and then handled exactly like
    geo_distance:, reusing its filter/distance_feature logic unchanged.
    """

    prefix: ClassVar[str] = "icsr_distance:"

    def _parse_value(self, field: str, value: str) -> tuple[float, float, str]:
        match = _ICRS_DISTANCE_VALUE_RE.match(value.strip())
        if not match:
            raise QuerystringValidationError(
                _(
                    "Invalid value %(value)r for parameter '%(param)s%(field)s'. "
                    "Expected '[ra,dec,distance]' (distance in degrees), "
                    "e.g. '[83.6,22.0,5]'.",
                    value=value,
                    param=self.prefix,
                    field=field,
                )
            )
        lat, lon = _ra_dec_to_lat_lon(float(match.group("ra")), float(match.group("dec")))
        distance_km = _degrees_to_km(float(match.group("distance")))
        return lat, lon, _format_km(distance_km)


#: Matches ``[ra,dec,ra,dec]`` or ``ra,dec,ra,dec`` (two opposite corners).
_ICRS_BOUNDING_BOX_VALUE_RE = re.compile(
    r"^\[?\s*(?P<ra1>[+-]?\d+(?:\.\d+)?)\s*,\s*(?P<dec1>[+-]?\d+(?:\.\d+)?)\s*,\s*"
    r"(?P<ra2>[+-]?\d+(?:\.\d+)?)\s*,\s*(?P<dec2>[+-]?\d+(?:\.\d+)?)\s*\]?$"
)


class IcrsBoundingBoxParam(GeoBoundingBoxParam):
    """Evaluate ``icsr_bounding_box:<field>=[ra,dec,ra,dec]`` query parameters.

    The two points are opposite corners of the box in ICRS right
    ascension/declination (degrees, any order). Each pair is converted to
    lat/lon and then handled exactly like geo_bounding_box:, reusing its
    normalization/filter/distance_feature logic unchanged.
    """

    prefix: ClassVar[str] = "icsr_bounding_box:"

    def _parse_value(self, field: str, value: str) -> tuple[float, float, float, float]:
        match = _ICRS_BOUNDING_BOX_VALUE_RE.match(value.strip())
        if not match:
            raise QuerystringValidationError(
                _(
                    "Invalid value %(value)r for parameter '%(param)s%(field)s'. "
                    "Expected '[ra,dec,ra,dec]', e.g. '[80,20,90,25]'.",
                    value=value,
                    param=self.prefix,
                    field=field,
                )
            )
        lat1, lon1 = _ra_dec_to_lat_lon(float(match.group("ra1")), float(match.group("dec1")))
        lat2, lon2 = _ra_dec_to_lat_lon(float(match.group("ra2")), float(match.group("dec2")))
        return lat1, lon1, lat2, lon2


def _icrs_shape_coords_to_lat_lon(ra: float, dec: float) -> tuple[float, float]:
    """Transform callback for shapely.ops.transform: WKT (ra, dec) -> (lon, lat)."""
    lat, lon = _ra_dec_to_lat_lon(ra, dec)
    return lon, lat


class IcrsShapeParam(GeoShapeParam):
    """Evaluate ``icsr_shape:<field>=[OP ]<WKT>`` query parameters.

    Like geo_shape:, but the WKT's x/y coordinates are read as ICRS right
    ascension/declination (degrees) rather than lon/lat, and remapped
    accordingly before being converted to GeoJSON, so it points at the same
    coordinates ICRSDumperExt actually indexed.
    """

    prefix: ClassVar[str] = "icsr_shape:"

    def _load_geometry(self, field: str, wkt_text: str) -> BaseGeometry:
        geometry = super()._load_geometry(field, wkt_text)
        return shapely_transform(_icrs_shape_coords_to_lat_lon, geometry)
