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
from functools import lru_cache
from typing import TYPE_CHECKING, Any, ClassVar, NamedTuple

from flask import current_app
from geopy.exc import GeopyError
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from invenio_i18n import gettext as _
from invenio_records_resources.services.errors import QuerystringValidationError
from invenio_records_resources.services.records.params.base import ParamInterpreter
from opensearch_dsl import Q
from shapely import wkt as shapely_wkt
from shapely.errors import ShapelyError
from shapely.geometry import mapping as shapely_mapping
from shapely.geometry import shape as shapely_shape

from oarepo_model.datatypes.spherical import icrs_shape_to_lon_lat, ra_dec_to_lat_lon

if TYPE_CHECKING:
    from collections.abc import Callable

    from opensearch_dsl.search import Search
    from shapely.geometry.base import BaseGeometry

#: Mean earth radius in kilometers, used to convert angular distances to km.
_EARTH_RADIUS_KM = 6371.0088


# NOTE: this talks to the public OpenStreetMap Nominatim instance by default.
# Its usage policy caps clients at ~1 request/second and asks for an
# application-specific user agent; both are configurable (NOMINATIM_USER_AGENT,
# NOMINATIM_MIN_DELAY_SECONDS) so a production deployment resolving many
# distinct place names can point this at a self-hosted/paid instance instead.
@lru_cache(maxsize=1)
def _get_geocode() -> Callable[..., Any]:
    """Lazily build a rate-limited Nominatim.geocode callable.

    Built lazily on first use (rather than at import time) since the user
    agent is derived from the current Flask app's configuration, which isn't
    available yet at import time. ``lru_cache`` makes it a process-wide
    singleton, built once and reused: the RateLimiter's "last call" timestamp
    needs to be shared across all callers for the rate limit to mean
    anything, and Nominatim's public instance rate-limits by client (i.e. by
    process), not by request or by app.
    """
    default_user_agent = f"Invenio RDM (CESNET flavour, {current_app.config.get('SITE_UI_URL', '')})"
    user_agent = current_app.config.get("NOMINATIM_USER_AGENT", default_user_agent)
    min_delay_seconds = current_app.config.get("NOMINATIM_MIN_DELAY_SECONDS", 1)
    geolocator = Nominatim(user_agent=user_agent)
    return RateLimiter(  # type: ignore[no-any-return]
        geolocator.geocode,
        min_delay_seconds=min_delay_seconds,
        swallow_exceptions=False,
    )


@lru_cache(maxsize=256)
def _nominatim_geocode_point(location_name: str) -> tuple[float, float]:
    """Resolve a place name to (lat, lon) using OpenStreetMap Nominatim."""
    location = _get_geocode()(location_name)
    if location is None:
        raise ValueError(location_name)
    return location.latitude, location.longitude


@lru_cache(maxsize=256)
def _nominatim_geocode_shape(location_name: str) -> dict[str, Any]:
    """Resolve a place name to a GeoJSON geometry using OpenStreetMap Nominatim."""
    location = _get_geocode()(location_name, geometry="geojson")
    if location is None or "geojson" not in location.raw:
        raise ValueError(location_name)
    return location.raw["geojson"]  # type: ignore[no-any-return]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute the great-circle distance between two points, in kilometers."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _normalize_latitude(lat: float) -> float:
    """Fold a latitude into the ``-90 <= lat <= 90`` range OpenSearch requires.

    The guard is load-bearing: without it the modulo carries the North Pole at
    90 over to -90, on the far side of the planet, and in-range values pick up
    float noise from the round trip. Both ends are genuine distinct places, so
    the range is closed, unlike longitude below.
    """
    if -90 <= lat <= 90:  # noqa: PLR2004
        return lat
    return (lat + 90) % 180 - 90


def _normalize_longitude(lon: float) -> float:
    """Fold a longitude into the ``[-180, 180)`` range OpenSearch requires.

    The guard keeps in-range values free of the float noise a 180-degree round
    trip adds, but stops short of +180, which is the same meridian as -180 and
    so folds rather than staying put.
    """
    if -180 <= lon < 180:  # noqa: PLR2004
        return lon
    return (lon + 180) % 360 - 180


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


class _PrefixedGeoParam(ParamInterpreter):
    """Base class for search parameter interpreters keyed by a fixed prefix.

    A subclass sets ``prefix`` and implements ``_apply_value`` to turn one
    raw ``prefix<field>=<value>`` occurrence into a change on the search.
    """

    #: Prefix of the query string parameter, e.g. ``geo_distance:metadata.location``.
    prefix: ClassVar[str]

    def apply(  # type: ignore[reportIncompatibleMethodOverride]
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

    def _geocode_point(self, field: str, location_name: str) -> tuple[float, float]:
        try:
            return _nominatim_geocode_point(location_name)
        except (ValueError, GeopyError) as error:
            raise QuerystringValidationError(
                _(
                    "Could not resolve location name %(location)r for parameter '%(param)s%(field)s'.",
                    location=location_name,
                    param=self.prefix,
                    field=field,
                )
            ) from error

    def _geocode_shape(self, field: str, location_name: str) -> dict[str, Any]:
        try:
            return _nominatim_geocode_shape(location_name)
        except (ValueError, GeopyError) as error:
            raise QuerystringValidationError(
                _(
                    "Could not resolve location name %(location)r for parameter '%(param)s%(field)s'.",
                    location=location_name,
                    param=self.prefix,
                    field=field,
                )
            ) from error


#: Matches ``[lon,lat,distance]`` or ``lon,lat,distance``, longitude before
#: latitude, the order RFC 7946 gives a GeoJSON position.
_DISTANCE_VALUE_RE = re.compile(
    r"^\[?\s*(?P<lon>[+-]?\d+(?:\.\d+)?)\s*,\s*(?P<lat>[+-]?\d+(?:\.\d+)?)\s*,\s*"
    r"(?P<distance>\d+(?:\.\d+)?\s*[a-zA-Z]+)\s*\]?$"
)

#: Matches a distance value such as ``50km`` or ``12.5mi``.
_DISTANCE_RE = re.compile(r"^\s*(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>[a-zA-Z]+)\s*$")

#: Matches ``[location name,distance]``. The location is matched lazily so
#: that, combined with the anchored end, it captures everything up to the
#: *last* comma - which lets the location itself contain commas (e.g. "Prague,
#: Czechia") while still correctly separating off the trailing distance.
_LOCATION_DISTANCE_VALUE_RE = re.compile(
    r"^\[?\s*(?P<location>.+?)\s*,\s*(?P<distance>\d+(?:\.\d+)?\s*[a-zA-Z]+)\s*\]?$",
    re.DOTALL,
)

#: Matches a bare number, used to decide whether a value's first component
#: looks like a coordinate or a place name.
_NUMBER_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")


class _PointDistance(NamedTuple):
    """A point and a distance around it, the point as ``[lon, lat]``.

    A named tuple because both coordinates are plain floats: as a bare tuple it
    was possible to hand ``_apply_value`` a transposed pair and have nothing,
    not even the type checker, notice.
    """

    lon: float
    lat: float
    distance: str


class GeoDistanceParam(_PrefixedGeoParam):
    """Evaluate ``geo_distance:<field>=[lon,lat,distance]`` query parameters.

    ``lon`` and ``lat`` are degrees and must lie in ``-180 <= lon <= 180`` and
    ``-90 <= lat <= 90``, the range OpenSearch's geo_point field accepts. They
    come in the longitude-first order of a GeoJSON position, which is *not* the
    latitude-first order of a 'geo' URI. ``distance`` is a positive number with
    a unit OpenSearch understands (``km``, ``m``, ``mi``, ...).

    For every occurrence of this parameter, records within ``distance`` of the
    point are kept (``geo_distance`` filter on ``field``), and records closer to
    it are additionally boosted in relevance via a ``distance_feature`` query,
    with the pivot set to a tenth of the requested distance.

    Instead of ``lon,lat``, a place name may be given, e.g.
    ``[Prague, Czechia,50km]``: if the part before the first comma doesn't
    parse as a number, everything up to the last comma is geocoded (via
    OpenStreetMap Nominatim) to get the point.
    """

    prefix: ClassVar[str] = "geo_distance:"

    #: Fraction of the requested distance used as the ``distance_feature`` pivot.
    pivot_divisor: ClassVar[int] = 10

    def _apply_value(self, search: Search, field: str, value: str) -> Search:
        point = self._parse_value(field, value)

        search = search.filter(
            "geo_distance",
            distance=point.distance,
            **{field: {"lat": point.lat, "lon": point.lon}},
        )
        return search.query(
            "bool",
            should=[
                Q(
                    "distance_feature",
                    field=field,
                    origin={"lat": point.lat, "lon": point.lon},
                    pivot=self._pivot(point.distance),
                )
            ],
        )

    def _parse_value(self, field: str, value: str) -> _PointDistance:
        value = value.strip()
        match = _DISTANCE_VALUE_RE.match(value)
        if match:
            return _PointDistance(
                lon=float(match.group("lon")),
                lat=float(match.group("lat")),
                distance=match.group("distance").replace(" ", ""),
            )

        # Not "[lon,lat,distance]": if the first component isn't a number,
        # treat everything up to the last comma as a place name (which may
        # itself contain commas, e.g. "Prague, Czechia") and geocode it.
        first_part = value.removeprefix("[").split(",", 1)[0].strip()
        location_match = _LOCATION_DISTANCE_VALUE_RE.match(value)
        if location_match and not _NUMBER_RE.match(first_part):
            # The geocoder answers latitude first, unlike the wire format.
            lat, lon = self._geocode_point(field, location_match.group("location"))
            return _PointDistance(
                lon=lon,
                lat=lat,
                distance=location_match.group("distance").replace(" ", ""),
            )

        raise QuerystringValidationError(
            _(
                "Invalid value %(value)r for parameter '%(param)s%(field)s'. "
                "Expected '[lon,lat,distance]' or '[location name,distance]', "
                "e.g. '[14.4,50.0,50km]' or '[Prague, Czechia,50km]'.",
                value=value,
                param=self.prefix,
                field=field,
            )
        )

    def _pivot(self, distance: str) -> str:
        match = _DISTANCE_RE.match(distance)
        assert match is not None  # noqa: S101 -- already validated by _parse_value
        pivot_value = round(float(match.group("value")) / self.pivot_divisor, 6)
        if pivot_value == int(pivot_value):
            pivot_value = int(pivot_value)
        return f"{pivot_value}{match.group('unit')}"


#: Matches ``[lon,lat,lon,lat]`` or ``lon,lat,lon,lat``: the two opposite
#: corners in the ``[west, south, east, north]`` axis order RFC 7946 defines
#: for a bounding box, longitude before latitude.
_BOUNDING_BOX_VALUE_RE = re.compile(
    r"^\[?\s*(?P<west>[+-]?\d+(?:\.\d+)?)\s*,\s*(?P<south>[+-]?\d+(?:\.\d+)?)\s*,\s*"
    r"(?P<east>[+-]?\d+(?:\.\d+)?)\s*,\s*(?P<north>[+-]?\d+(?:\.\d+)?)\s*\]?$"
)


class _BoundingBox(NamedTuple):
    """A box's corners as ``[west, south, east, north]``, the GeoJSON order.

    A named tuple because all four corners are plain floats: as a bare tuple it
    was possible to hand ``_apply_value`` a transposed pair and have nothing,
    not even the type checker, notice.
    """

    west: float
    south: float
    east: float
    north: float


class GeoBoundingBoxParam(_PrefixedGeoParam):
    """Evaluate ``geo_bounding_box:<field>=[lon,lat,lon,lat]`` query parameters.

    The corners follow the axis order RFC 7946 defines for a bounding box,
    ``[west, south, east, north]``, longitude before latitude, the way GeoJSON
    positions are ordered too. This is *not* the latitude-first order of a
    'geo' URI. Coordinates are degrees and must preferably lie in
    ``-90 <= lat <= 90`` and ``-180 <= lon <= 180``, the range OpenSearch's
    geo_point field accepts.

    The two points are the box's southwesterly and northeasterly corners, given
    in a strict order: the first must have the lower latitude, and the longitude
    range always runs *eastward* from the first point to the second one. That is
    RFC 7946 Section 5.2, which likewise lets a crossing box have an east
    longitude smaller than its own west one. The order is therefore meaningful:
    ``[170,49.5,-170,50.5]`` is a 20-degree-wide box crossing the antimeridian,
    while ``[-170,49.5,170,50.5]`` is the complementary box spanning 340 degrees
    of longitude.

    Latitude does not wrap around the way longitude does, so a box cannot run
    past a pole; it ends at one. RFC 7946 Section 5.3 writes a box reaching the
    North Pole as ``[-180, minlat, 180, 90]``, and this parameter accepts that
    shape: west and east then share a meridian, which is read as the whole
    globe rather than as a box of no width, and OpenSearch is given the full
    longitude span it needs to match a polar cap.

    For every occurrence of this parameter, records inside the box are kept
    (``geo_bounding_box`` filter on ``field``), and records closer to the
    center of the box are additionally boosted in relevance via a
    ``distance_feature`` query, with the pivot set to half of the box's
    diagonal, converted from degrees to kilometers.
    """

    prefix: ClassVar[str] = "geo_bounding_box:"

    def _apply_value(self, search: Search, field: str, value: str) -> Search:
        box = self._parse_value(field, value)
        south = _normalize_latitude(box.south)
        north = _normalize_latitude(box.north)
        west = _normalize_longitude(box.west)
        east = _normalize_longitude(box.east)

        # West and east landing on the same meridian means the box runs all the
        # way round, not nowhere: [-180, minlat, 180, maxlat] is how RFC 7946
        # writes a box reaching a pole, and 180 folds onto -180, so that is the
        # shape it arrives in. OpenSearch rejects a zero-width box outright, so
        # the full ring is spelled out for it.
        full_ring = west == east
        west_lon, east_lon = (-180.0, 180.0) if full_ring else (west, east)
        lon_span = 360.0 if full_ring else (east - west) % 360

        # A GeoJSON bbox is named by its southwesterly and northeasterly
        # corners, but OpenSearch names the opposite diagonal, so the values
        # have to be recombined: it takes the west longitude from top_left and
        # the east one from bottom_right, and reads top_left lon > bottom_right
        # lon as a box crossing the antimeridian, which is west > east.
        top_left = {"lat": north, "lon": west_lon}
        bottom_right = {"lat": south, "lon": east_lon}

        # The center lies in the middle of the eastward longitude arc, not at
        # the plain average of the two longitudes: the average of 170 and -170
        # is 0, halfway around the world away from a 20-degree-wide box.
        center_lat = (south + north) / 2
        center_lon = _normalize_longitude(west + lon_span / 2)
        center = {"lat": center_lat, "lon": center_lon}

        # Half of the diagonal is the distance from the center to a corner.
        # The distance between the two supplied corners cannot be used, because
        # a great circle always takes the short way round: it reports the same
        # length for a box and for its 360-degrees-minus-itself complement,
        # which is what made antimeridian crossing unrepresentable.
        half_diagonal_km = _haversine_km(center_lat, center_lon, south, west)

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

    def _parse_value(self, field: str, value: str) -> _BoundingBox:
        """Parse the value into the box's four corners.

        The named regex groups are read into ``_BoundingBox`` by keyword, so no
        positional step is left where corners could be transposed.
        """
        match = _BOUNDING_BOX_VALUE_RE.match(value.strip())
        if not match:
            raise QuerystringValidationError(
                _(
                    "Invalid value %(value)r for parameter '%(param)s%(field)s'. "
                    "Expected '[lon,lat,lon,lat]' as '[west,south,east,north]', "
                    "e.g. '[14.2,49.9,14.6,50.2]'.",
                    value=value,
                    param=self.prefix,
                    field=field,
                )
            )

        box = _BoundingBox(
            west=float(match.group("west")),
            south=float(match.group("south")),
            east=float(match.group("east")),
            north=float(match.group("north")),
        )

        if box.south > box.north:
            raise QuerystringValidationError(
                _(
                    "Invalid value %(value)r for parameter '%(param)s%(field)s'. "
                    "The southwesterly point must have the lower latitude, "
                    "got %(south)s and %(north)s. Unlike longitude, latitude "
                    "does not wrap around; to select a polar cap, run the box "
                    "to the pole instead, e.g. '[-180,66.5,180,90]'.",
                    value=value,
                    param=self.prefix,
                    field=field,
                    south=box.south,
                    north=box.north,
                )
            )

        return box


#: Relations accepted by the OpenSearch geo_shape query.
_GEO_SHAPE_OPERATIONS = frozenset({"INTERSECTS", "DISJOINT", "WITHIN", "CONTAINS"})
_DEFAULT_GEO_SHAPE_OPERATION = "INTERSECTS"

#: Splits an optional leading operation keyword from the rest of the value (the WKT).
_GEO_SHAPE_OP_RE = re.compile(r"^\s*(?P<op>[A-Za-z]+)\s+(?P<rest>.+)$", re.DOTALL)


#: Matches the start of a WKT geometry, e.g. "POLYGON (" or "MULTIPOINT Z(".
#: Used to tell WKT apart from a place name, which never looks like this.
_WKT_TYPE_RE = re.compile(
    r"^(?:POINT|LINESTRING|POLYGON|MULTIPOINT|MULTILINESTRING|MULTIPOLYGON|"
    r"GEOMETRYCOLLECTION|CIRCULARSTRING|COMPOUNDCURVE|CURVEPOLYGON|MULTICURVE|"
    r"MULTISURFACE|TRIANGLE|TIN|POLYHEDRALSURFACE)\s*(?:Z|M|ZM)?\s*\(",
    re.IGNORECASE,
)


def _looks_like_wkt(text: str) -> bool:
    """Return whether ``text`` starts like a WKT geometry rather than a place name."""
    return _WKT_TYPE_RE.match(text.strip()) is not None


class GeoShapeParam(_PrefixedGeoParam):
    """Evaluate ``geo_shape:<field>=[OP ]<WKT>`` query parameters.

    The geometry's coordinates are ``(lon, lat)`` pairs in degrees, within
    ``-180 <= lon <= 180`` and ``-90 <= lat <= 90``, the range OpenSearch's
    geo_shape field accepts.

    ``OP`` is one of ``INTERSECTS`` (the default), ``DISJOINT``, ``WITHIN`` or
    ``CONTAINS`` and becomes the ``relation`` of a ``geo_shape`` filter on
    ``field``. The WKT geometry (e.g. ``POLYGON ((...))``) is parsed and
    converted to GeoJSON with shapely, since that's the format OpenSearch's
    geo_shape query expects for the ``shape`` value.

    Instead of WKT, a place name may be given, e.g. ``INTERSECTS Prague,
    Czechia``: if the text doesn't start like a WKT geometry, it's geocoded
    (via OpenStreetMap Nominatim) to a GeoJSON shape.
    """

    prefix: ClassVar[str] = "geo_shape:"

    #: Whether a value that isn't valid WKT may be resolved as a place name
    #: via geocoding. ICRS coordinates have no such notion, so IcrsShapeParam
    #: turns this off and only ever accepts WKT.
    allow_location_name: ClassVar[bool] = True

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
        if self.allow_location_name and not _looks_like_wkt(wkt_text):
            return shapely_shape(self._geocode_shape(field, wkt_text))

        try:
            return shapely_wkt.loads(wkt_text)
        except ShapelyError as error:
            if self.allow_location_name:
                expected = (
                    "Expected '[OP ]<WKT>' or '[OP ]<place name>', e.g. "
                    "'WITHIN POLYGON ((0 0, 1 0, 1 1, 0 0))' or 'INTERSECTS Prague, Czechia'."
                )
            else:
                expected = "Expected '[OP ]<WKT>', e.g. 'WITHIN POLYGON ((0 0, 1 0, 1 1, 0 0))'."
            raise QuerystringValidationError(
                _(
                    "Invalid value %(value)r for parameter '%(param)s%(field)s'. %(expected)s",
                    value=wkt_text,
                    param=self.prefix,
                    field=field,
                    expected=expected,
                )
            ) from error


#: Matches ``[ra,dec,distance]`` or ``ra,dec,distance`` (distance in degrees, no unit).
_ICRS_DISTANCE_VALUE_RE = re.compile(
    r"^\[?\s*(?P<ra>[+-]?\d+(?:\.\d+)?)\s*,\s*(?P<dec>[+-]?\d+(?:\.\d+)?)\s*,\s*"
    r"(?P<distance>\d+(?:\.\d+)?)\s*\]?$"
)


class IcrsDistanceParam(GeoDistanceParam):
    """Evaluate ``icrs_distance:<field>=[ra,dec,distance]`` query parameters.

    Keeps records within ``distance`` of the given point and boosts the ones
    closer to it, just like geo_distance:, but reads the point as ICRS right
    ascension/declination in degrees, within ``0 <= ra < 360`` and
    ``-90 <= dec <= 90``. Right ascension comes first, which is the
    longitude-first order of a GeoJSON position that geo_distance: uses too.

    ``distance`` is a great-circle angle in degrees rather than a length, so
    it takes no unit suffix and must be within ``0 <= distance <= 180``:
    ``[83.6,22.0,5]`` selects everything within 5 degrees of the Crab Nebula.
    """

    prefix: ClassVar[str] = "icrs_distance:"

    def _parse_value(self, field: str, value: str) -> _PointDistance:
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
        # geo_distance: works in Earth lat/lon and in kilometers, so both
        # halves of the value are translated into those terms before it takes
        # over; see _degrees_to_km for why an angle may be handed to it as a
        # kilometer distance.
        lat, lon = ra_dec_to_lat_lon(float(match.group("ra")), float(match.group("dec")))
        distance_km = _degrees_to_km(float(match.group("distance")))
        # ra_dec_to_lat_lon answers latitude first, unlike the wire format.
        return _PointDistance(lon=lon, lat=lat, distance=_format_km(distance_km))


#: Matches ``[ra,dec,ra,dec]`` or ``ra,dec,ra,dec`` (two opposite corners).
_ICRS_BOUNDING_BOX_VALUE_RE = re.compile(
    r"^\[?\s*(?P<ra1>[+-]?\d+(?:\.\d+)?)\s*,\s*(?P<dec1>[+-]?\d+(?:\.\d+)?)\s*,\s*"
    r"(?P<ra2>[+-]?\d+(?:\.\d+)?)\s*,\s*(?P<dec2>[+-]?\d+(?:\.\d+)?)\s*\]?$"
)


class IcrsBoundingBoxParam(GeoBoundingBoxParam):
    """Evaluate ``icrs_bounding_box:<field>=[ra,dec,ra,dec]`` query parameters.

    Keeps records inside the box and boosts the ones nearer its center, just
    like geo_bounding_box:, but with the corners given as ICRS right
    ascension/declination in degrees, within ``0 <= ra < 360`` and
    ``-90 <= dec <= 90``.

    Right ascension comes first, so this already has the longitude-first
    ``[west, south, east, north]`` axis order RFC 7946 gives a GeoJSON bbox,
    which is the order geo_bounding_box: expects as well.

    The two points are opposite corners, and their order carries the box's
    meaning just as it does for geo_bounding_box:, whose rules apply here too.
    Ranges running over the 0/360 wrap are fine: ``[350,20,10,25]`` is a
    20-degree-wide box around ra 0, whereas ``[10,20,350,25]`` is its
    340-degree-wide complement.
    """

    prefix: ClassVar[str] = "icrs_bounding_box:"

    def _parse_value(self, field: str, value: str) -> _BoundingBox:
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
        # Passed on to geo_bounding_box: in the lat/lon space it queries in,
        # which is the same space ICRSDumperExt indexes ICRS points in. Note
        # that the fold in ra_dec_to_lat_lon puts the longitude antimeridian at
        # ra 180, not at ra 0, so which ranges cross it differs from geo. It
        # answers in (lat, lon) order, the other way round to the box corners,
        # which is why the two values cross over as they get bound.
        south, west = ra_dec_to_lat_lon(float(match.group("ra1")), float(match.group("dec1")))
        north, east = ra_dec_to_lat_lon(float(match.group("ra2")), float(match.group("dec2")))
        return _BoundingBox(west=west, south=south, east=east, north=north)


def _icrs_shape_coords_to_lat_lon(ra: float, dec: float, z: float | None = None) -> tuple[float, float]:
    """Transform callback for shapely.ops.transform: WKT (ra, dec) -> (lon, lat).

    ICRS shapes are always 2D, so the optional `z` shapely.ops.transform may
    pass (see its docstring's `def id_func(x, y, z=None)` convention) is
    accepted but ignored.
    """
    del z
    lat, lon = ra_dec_to_lat_lon(ra, dec)
    return lon, lat


class IcrsShapeParam(GeoShapeParam):
    """Evaluate ``icrs_shape:<field>=[OP ]<WKT>`` query parameters.

    Like geo_shape:, but the WKT's x/y coordinates are read as ICRS right
    ascension/declination in degrees rather than as lon/lat, within
    ``0 <= ra < 360`` and ``-90 <= dec <= 90``.

    A value that doesn't parse as WKT is an error: there are no place names on
    the celestial sphere, so the geocoding fallback geo_shape: offers for those
    is turned off here.
    """

    prefix: ClassVar[str] = "icrs_shape:"

    #: ICRS coordinates aren't Earth place names, so never try to geocode them.
    allow_location_name: ClassVar[bool] = False

    def _load_geometry(self, field: str, wkt_text: str) -> BaseGeometry:
        # The remap puts the shape into the lat/lon space the ICRS points were
        # indexed in, so query and index agree on what a coordinate means.
        geometry = super()._load_geometry(field, wkt_text)
        return icrs_shape_to_lon_lat(geometry)
