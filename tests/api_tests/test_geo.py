#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import pytest
from geopy.exc import GeocoderTimedOut
from invenio_records_resources.services.errors import QuerystringValidationError
from opensearch_dsl import Search
from opensearchpy.exceptions import RequestError

from oarepo_model.presets.records_resources.services.records.params import spherical
from oarepo_model.presets.records_resources.services.records.params.spherical import (
    GeoBoundingBoxParam,
    GeoDistanceParam,
    GeoShapeParam,
    _format_km,
    _get_geocode,
    _haversine_km,
)

# Prague-ish origin used as the search point in the tests below.
ORIGIN_LAT = 50.087
ORIGIN_LON = 14.420

#: Kilometers per degree of latitude, used to place points at a known
#: north-south distance from ORIGIN without relying on ES's own distance
#: computation to build the fixture data.
KM_PER_DEGREE_LAT = 111.32


def _point_south_of_origin(km: float) -> dict[str, float]:
    return {"lat": ORIGIN_LAT - km / KM_PER_DEGREE_LAT, "lon": ORIGIN_LON}


def test_geo_distance_param_filters_and_boosts_by_distance(
    app,
    geo_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    service = geo_model.proxies.current_service
    Record = geo_model.Record

    near = service.create(
        identity_simple,
        {"metadata": {"title": "Near", "location": _point_south_of_origin(5)}},
    )
    mid = service.create(
        identity_simple,
        {"metadata": {"title": "Mid", "location": _point_south_of_origin(35)}},
    )
    far = service.create(
        identity_simple,
        {"metadata": {"title": "Far", "location": _point_south_of_origin(300)}},
    )

    Record.index.refresh()

    search_dsl = service.create_search(identity_simple, Record, service.config.search)
    search_dsl = GeoDistanceParam(service.config.search).apply(
        identity_simple,
        search_dsl,
        {"geo_distance:metadata.location": [f"[{ORIGIN_LAT},{ORIGIN_LON},50km]"]},
    )
    result = search_dsl.execute()

    hit_ids = [hit.id for hit in result]
    assert set(hit_ids) == {near.id, mid.id}
    assert far.id not in hit_ids

    # the closer record must score higher due to the distance_feature boost
    assert hit_ids.index(near.id) < hit_ids.index(mid.id)


def test_geo_distance_param_via_service_search(
    app,
    geo_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    """Exercise the full service.search() flow, as a real request would.

    The default SearchRequestArgsSchema buckets every query-string key it
    doesn't recognize (including geo_distance:<field>) into params["facets"],
    so this also proves GeoPreset wires GeoDistanceParam in *before* the
    facets interpreter, which would otherwise silently drop the key.
    """
    service = geo_model.proxies.current_service
    Record = geo_model.Record

    near = service.create(
        identity_simple,
        {"metadata": {"title": "Near", "location": _point_south_of_origin(5)}},
    )
    far = service.create(
        identity_simple,
        {"metadata": {"title": "Far", "location": _point_south_of_origin(300)}},
    )
    Record.index.refresh()

    result = service.search(
        identity_simple,
        facets={"geo_distance:metadata.location": [f"[{ORIGIN_LAT},{ORIGIN_LON},50km]"]},
    )

    hit_ids = {hit["id"] for hit in result.hits}
    assert hit_ids == {near.id}
    assert far.id not in hit_ids


def test_geo_distance_param_removes_key_from_params():
    params = {"geo_distance:metadata.location": ["[1,2,10km]"], "other": ["x"]}

    GeoDistanceParam(config=None).apply(None, Search(), params)

    assert params == {"other": ["x"]}


def test_geo_distance_param_removes_key_from_facets_bucket():
    """Must also handle geo_distance:<field> nested in params["facets"].

    That's where the default SearchRequestArgsSchema puts unrecognized
    query-string keys for real requests.
    """
    params = {"facets": {"geo_distance:metadata.location": ["[1,2,10km]"], "other": ["x"]}}

    GeoDistanceParam(config=None).apply(None, Search(), params)

    assert params == {"facets": {"other": ["x"]}}


def test_geo_distance_param_invalid_value_raises():
    with pytest.raises(QuerystringValidationError):
        GeoDistanceParam(config=None).apply(
            None,
            Search(),
            {"geo_distance:metadata.location": ["not-a-point"]},
        )


@pytest.mark.parametrize(
    ("distance", "expected_pivot"),
    [
        ("50km", "5km"),
        ("10m", "1m"),
        ("12.5mi", "1.25mi"),
        ("1km", "0.1km"),
    ],
)
def test_geo_distance_param_pivot(distance, expected_pivot):
    interpreter = GeoDistanceParam(config=None)
    assert interpreter._pivot(distance) == expected_pivot  # noqa: SLF001


# A ~1x1 degree box roughly covering Prague. lat: 49.5-50.5, lon: 14.0-15.0.
BBOX_TOP_LAT = 50.5
BBOX_BOTTOM_LAT = 49.5
BBOX_LEFT_LON = 14.0
BBOX_RIGHT_LON = 15.0
BBOX_VALUE = f"[{BBOX_TOP_LAT},{BBOX_LEFT_LON},{BBOX_BOTTOM_LAT},{BBOX_RIGHT_LON}]"


def test_geo_bounding_box_param_filters_and_boosts_by_distance(
    app,
    geo_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    service = geo_model.proxies.current_service
    Record = geo_model.Record

    center = service.create(
        identity_simple,
        {"metadata": {"title": "Center", "location": {"lat": 50.0, "lon": 14.5}}},
    )
    corner = service.create(
        identity_simple,
        {"metadata": {"title": "Corner", "location": {"lat": 49.55, "lon": 14.05}}},
    )
    outside = service.create(
        identity_simple,
        {"metadata": {"title": "Outside", "location": {"lat": 52.0, "lon": 14.5}}},
    )

    Record.index.refresh()

    search_dsl = service.create_search(identity_simple, Record, service.config.search)
    search_dsl = GeoBoundingBoxParam(service.config.search).apply(
        identity_simple,
        search_dsl,
        {"geo_bounding_box:metadata.location": [BBOX_VALUE]},
    )
    result = search_dsl.execute()

    hit_ids = [hit.id for hit in result]
    assert set(hit_ids) == {center.id, corner.id}
    assert outside.id not in hit_ids

    # the record closer to the box's center must score higher
    assert hit_ids.index(center.id) < hit_ids.index(corner.id)


def test_geo_bounding_box_param_via_service_search(
    app,
    geo_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    """Exercise the full service.search() flow, as a real request would.

    Like geo_distance:<field>, geo_bounding_box:<field> is bucketed into
    params["facets"] by the default SearchRequestArgsSchema, so this also
    proves GeoPreset wires GeoBoundingBoxParam in before the facets
    interpreter consumes that bucket.
    """
    service = geo_model.proxies.current_service
    Record = geo_model.Record

    inside = service.create(
        identity_simple,
        {"metadata": {"title": "Inside", "location": {"lat": 50.0, "lon": 14.5}}},
    )
    outside = service.create(
        identity_simple,
        {"metadata": {"title": "Outside", "location": {"lat": 52.0, "lon": 14.5}}},
    )
    Record.index.refresh()

    result = service.search(
        identity_simple,
        facets={"geo_bounding_box:metadata.location": [BBOX_VALUE]},
    )

    hit_ids = {hit["id"] for hit in result.hits}
    assert hit_ids == {inside.id}
    assert outside.id not in hit_ids


def test_geo_bounding_box_param_removes_key_from_params():
    params = {"geo_bounding_box:metadata.location": ["[1,1,0,2]"], "other": ["x"]}

    GeoBoundingBoxParam(config=None).apply(None, Search(), params)

    assert params == {"other": ["x"]}


def test_geo_bounding_box_param_removes_key_from_facets_bucket():
    """Must also handle geo_bounding_box:<field> nested in params["facets"]."""
    params = {"facets": {"geo_bounding_box:metadata.location": ["[1,1,0,2]"], "other": ["x"]}}

    GeoBoundingBoxParam(config=None).apply(None, Search(), params)

    assert params == {"facets": {"other": ["x"]}}


def test_geo_bounding_box_param_invalid_value_raises():
    with pytest.raises(QuerystringValidationError):
        GeoBoundingBoxParam(config=None).apply(
            None,
            Search(),
            {"geo_bounding_box:metadata.location": ["not-a-box"]},
        )


@pytest.mark.parametrize(
    "corners",
    [
        (BBOX_TOP_LAT, BBOX_LEFT_LON, BBOX_BOTTOM_LAT, BBOX_RIGHT_LON),
        (BBOX_BOTTOM_LAT, BBOX_RIGHT_LON, BBOX_TOP_LAT, BBOX_LEFT_LON),  # opposite diagonal
    ],
)
def test_geo_bounding_box_param_normalizes_corners(corners):
    lat1, lon1, lat2, lon2 = corners
    value = f"[{lat1},{lon1},{lat2},{lon2}]"

    search = GeoBoundingBoxParam(config=None).apply(
        None,
        Search(),
        {"geo_bounding_box:metadata.location": [value]},
    )

    query = search.to_dict()["query"]["bool"]
    assert query["filter"][0]["geo_bounding_box"]["metadata.location"] == {
        "top_left": {"lat": BBOX_TOP_LAT, "lon": BBOX_LEFT_LON},
        "bottom_right": {"lat": BBOX_BOTTOM_LAT, "lon": BBOX_RIGHT_LON},
    }
    assert query["must"][0]["distance_feature"]["origin"] == {"lat": 50.0, "lon": 14.5}
    # same diagonal length (and thus the same pivot) regardless of corner order
    assert query["must"][0]["distance_feature"]["pivot"] == "66.091km"


def test_haversine_km_known_distance():
    # ~111.19 km per degree of longitude at the equator
    assert _haversine_km(0, 0, 0, 1) == pytest.approx(111.19, abs=0.05)
    # symmetric regardless of point order
    assert _haversine_km(1, 2, 3, 4) == pytest.approx(_haversine_km(3, 4, 1, 2))


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (5.0, "5km"),
        (5.1234, "5.123km"),
        (0.1, "0.1km"),
    ],
)
def test_format_km(value, expected):
    assert _format_km(value) == expected


# A polygon roughly covering the same area as BBOX_VALUE above.
GEO_SHAPE_POLYGON_WKT = (
    f"POLYGON (({BBOX_LEFT_LON} {BBOX_BOTTOM_LAT}, {BBOX_RIGHT_LON} {BBOX_BOTTOM_LAT}, "
    f"{BBOX_RIGHT_LON} {BBOX_TOP_LAT}, {BBOX_LEFT_LON} {BBOX_TOP_LAT}, "
    f"{BBOX_LEFT_LON} {BBOX_BOTTOM_LAT}))"
)


def test_geo_shape_param_filters_records(
    app,
    geo_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    service = geo_model.proxies.current_service
    Record = geo_model.Record

    inside = service.create(
        identity_simple,
        {"metadata": {"title": "Inside", "location": {"lat": 50.0, "lon": 14.5}}},
    )
    outside = service.create(
        identity_simple,
        {"metadata": {"title": "Outside", "location": {"lat": 52.0, "lon": 14.5}}},
    )
    Record.index.refresh()

    search_dsl = service.create_search(identity_simple, Record, service.config.search)
    # no explicit operation: defaults to INTERSECTS, the only relation that
    # OpenSearch allows against a geo_point-mapped field (see
    # test_geo_shape_param_rejects_relations_unsupported_by_geo_point below)
    search_dsl = GeoShapeParam(service.config.search).apply(
        identity_simple,
        search_dsl,
        {"geo_shape:metadata.location": [GEO_SHAPE_POLYGON_WKT]},
    )
    result = search_dsl.execute()

    hit_ids = {hit.id for hit in result}
    assert hit_ids == {inside.id}
    assert outside.id not in hit_ids


def test_geo_shape_param_via_service_search(
    app,
    geo_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    """Exercise the full service.search() flow, as a real request would."""
    service = geo_model.proxies.current_service
    Record = geo_model.Record

    inside = service.create(
        identity_simple,
        {"metadata": {"title": "Inside", "location": {"lat": 50.0, "lon": 14.5}}},
    )
    outside = service.create(
        identity_simple,
        {"metadata": {"title": "Outside", "location": {"lat": 52.0, "lon": 14.5}}},
    )
    Record.index.refresh()

    result = service.search(
        identity_simple,
        facets={"geo_shape:metadata.location": [f"INTERSECTS {GEO_SHAPE_POLYGON_WKT}"]},
    )

    hit_ids = {hit["id"] for hit in result.hits}
    assert hit_ids == {inside.id}
    assert outside.id not in hit_ids


def test_geo_shape_param_rejects_relations_unsupported_by_geo_point(
    app,
    geo_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    """WITHIN/CONTAINS/DISJOINT only apply to geo_shape-mapped fields.

    OpenSearch itself enforces this (a geo_point field only supports
    INTERSECTS), so the interpreter builds the query as requested and lets
    OpenSearch reject it, the same way the other geo params defer field-type
    validation to the search engine.
    """
    service = geo_model.proxies.current_service
    Record = geo_model.Record
    service.create(
        identity_simple,
        {"metadata": {"title": "P", "location": {"lat": 50.0, "lon": 14.5}}},
    )
    Record.index.refresh()

    search_dsl = service.create_search(identity_simple, Record, service.config.search)
    search_dsl = GeoShapeParam(service.config.search).apply(
        identity_simple,
        search_dsl,
        {"geo_shape:metadata.location": [f"WITHIN {GEO_SHAPE_POLYGON_WKT}"]},
    )
    with pytest.raises(RequestError):
        search_dsl.execute()


def test_geo_shape_param_removes_key_from_params():
    params = {"geo_shape:metadata.location": ["POINT (14.5 50.0)"], "other": ["x"]}

    GeoShapeParam(config=None).apply(None, Search(), params)

    assert params == {"other": ["x"]}


def test_geo_shape_param_removes_key_from_facets_bucket():
    """Must also handle geo_shape:<field> nested in params["facets"]."""
    params = {"facets": {"geo_shape:metadata.location": ["POINT (14.5 50.0)"], "other": ["x"]}}

    GeoShapeParam(config=None).apply(None, Search(), params)

    assert params == {"facets": {"other": ["x"]}}


def test_geo_shape_param_invalid_value_raises():
    with pytest.raises(QuerystringValidationError):
        GeoShapeParam(config=None).apply(
            None,
            Search(),
            {"geo_shape:metadata.location": ["not a shape"]},
        )


def test_geo_shape_param_defaults_to_intersects():
    search = GeoShapeParam(config=None).apply(
        None,
        Search(),
        {"geo_shape:metadata.location": ["POINT (14.5 50.0)"]},
    )

    shape_query = search.to_dict()["query"]["bool"]["filter"][0]["geo_shape"]["metadata.location"]
    assert shape_query == {
        "shape": {"type": "Point", "coordinates": (14.5, 50.0)},
        "relation": "intersects",
    }


@pytest.mark.parametrize("operation", ["INTERSECTS", "DISJOINT", "WITHIN", "CONTAINS", "within"])
def test_geo_shape_param_explicit_operation(operation):
    search = GeoShapeParam(config=None).apply(
        None,
        Search(),
        {"geo_shape:metadata.location": [f"{operation} POINT (14.5 50.0)"]},
    )

    shape_query = search.to_dict()["query"]["bool"]["filter"][0]["geo_shape"]["metadata.location"]
    assert shape_query["relation"] == operation.lower()


# --- geo_distance:/geo_shape: place-name (Nominatim) resolution ---
#
# These mock the module-level _nominatim_geocode_point/_nominatim_geocode_shape
# functions rather than hitting the real OpenStreetMap Nominatim service, to
# keep the tests fast, offline and deterministic.

PRAGUE_LAT, PRAGUE_LON = 50.0755, 14.4378


def test_geo_distance_param_resolves_location_name(monkeypatch):
    calls = []

    def fake_geocode_point(location_name: str) -> tuple[float, float]:
        calls.append(location_name)
        return PRAGUE_LAT, PRAGUE_LON

    monkeypatch.setattr(spherical, "_nominatim_geocode_point", fake_geocode_point)

    search = GeoDistanceParam(config=None).apply(
        None,
        Search(),
        {"geo_distance:metadata.location": ["[Prague, Czechia,50km]"]},
    )

    # the location may itself contain a comma, so everything up to the last
    # comma must be passed to the geocoder, not just the first component
    assert calls == ["Prague, Czechia"]
    geo_distance = search.to_dict()["query"]["bool"]["filter"][0]["geo_distance"]
    assert geo_distance == {
        "distance": "50km",
        "metadata.location": {"lat": PRAGUE_LAT, "lon": PRAGUE_LON},
    }


def test_geo_distance_param_location_name_without_brackets(monkeypatch):
    monkeypatch.setattr(spherical, "_nominatim_geocode_point", lambda _name: (PRAGUE_LAT, PRAGUE_LON))

    search = GeoDistanceParam(config=None).apply(
        None,
        Search(),
        {"geo_distance:metadata.location": ["Prague, Czechia,50km"]},
    )

    geo_distance = search.to_dict()["query"]["bool"]["filter"][0]["geo_distance"]
    assert geo_distance["metadata.location"] == {"lat": PRAGUE_LAT, "lon": PRAGUE_LON}


def test_geo_distance_param_numeric_coordinates_are_not_geocoded(monkeypatch):
    def fail(_name: str) -> tuple[float, float]:
        raise AssertionError("should not geocode numeric lat/lon")

    monkeypatch.setattr(spherical, "_nominatim_geocode_point", fail)

    GeoDistanceParam(config=None).apply(
        None,
        Search(),
        {"geo_distance:metadata.location": ["[50.0,14.4,50km]"]},
    )


def test_geo_distance_param_location_not_found_raises(monkeypatch):
    def not_found(location_name: str) -> tuple[float, float]:
        raise ValueError(location_name)

    monkeypatch.setattr(spherical, "_nominatim_geocode_point", not_found)

    with pytest.raises(QuerystringValidationError):
        GeoDistanceParam(config=None).apply(
            None,
            Search(),
            {"geo_distance:metadata.location": ["[Nowhereville,50km]"]},
        )


def test_geo_distance_param_geocoder_error_raises(monkeypatch):
    def timed_out(_name: str) -> tuple[float, float]:
        raise GeocoderTimedOut("timed out")

    monkeypatch.setattr(spherical, "_nominatim_geocode_point", timed_out)

    with pytest.raises(QuerystringValidationError):
        GeoDistanceParam(config=None).apply(
            None,
            Search(),
            {"geo_distance:metadata.location": ["[Prague, Czechia,50km]"]},
        )


def test_geo_shape_param_resolves_location_name(monkeypatch):
    calls = []
    prague_geojson = {"type": "Point", "coordinates": [PRAGUE_LON, PRAGUE_LAT]}

    def fake_geocode_shape(location_name: str) -> dict:
        calls.append(location_name)
        return prague_geojson

    monkeypatch.setattr(spherical, "_nominatim_geocode_shape", fake_geocode_shape)

    search = GeoShapeParam(config=None).apply(
        None,
        Search(),
        {"geo_shape:metadata.location": ["WITHIN Prague, Czechia"]},
    )

    assert calls == ["Prague, Czechia"]
    shape_query = search.to_dict()["query"]["bool"]["filter"][0]["geo_shape"]["metadata.location"]
    # the geocoded GeoJSON is round-tripped through shapely (shape() then
    # mapping()) so it comes out with tuple coordinates, not the original lists
    assert shape_query == {
        "shape": {"type": "Point", "coordinates": (PRAGUE_LON, PRAGUE_LAT)},
        "relation": "within",
    }


def test_geo_shape_param_location_name_defaults_to_intersects(monkeypatch):
    prague_geojson = {"type": "Point", "coordinates": [PRAGUE_LON, PRAGUE_LAT]}
    monkeypatch.setattr(spherical, "_nominatim_geocode_shape", lambda _name: prague_geojson)

    search = GeoShapeParam(config=None).apply(
        None,
        Search(),
        {"geo_shape:metadata.location": ["Prague, Czechia"]},
    )

    shape_query = search.to_dict()["query"]["bool"]["filter"][0]["geo_shape"]["metadata.location"]
    assert shape_query["relation"] == "intersects"


def test_geo_shape_param_wkt_is_not_geocoded(monkeypatch):
    def fail(_name: str) -> dict:
        raise AssertionError("should not geocode a valid WKT value")

    monkeypatch.setattr(spherical, "_nominatim_geocode_shape", fail)

    GeoShapeParam(config=None).apply(
        None,
        Search(),
        {"geo_shape:metadata.location": ["POLYGON ((0 0, 1 0, 1 1, 0 0))"]},
    )


def test_geo_shape_param_location_not_found_raises(monkeypatch):
    def not_found(location_name: str) -> dict:
        raise ValueError(location_name)

    monkeypatch.setattr(spherical, "_nominatim_geocode_shape", not_found)

    with pytest.raises(QuerystringValidationError):
        GeoShapeParam(config=None).apply(
            None,
            Search(),
            {"geo_shape:metadata.location": ["Nowhereville"]},
        )


# --- _get_geocode() itself: lazy construction, config-driven, no network call ---


def test_get_geocode_uses_configured_user_agent(app):
    _get_geocode.cache_clear()
    app.config["NOMINATIM_USER_AGENT"] = "my-custom-agent"
    try:
        with app.app_context():
            geocode = _get_geocode()
        assert geocode.func.__self__.headers["User-Agent"] == "my-custom-agent"
    finally:
        del app.config["NOMINATIM_USER_AGENT"]
        _get_geocode.cache_clear()


def test_get_geocode_default_user_agent_includes_site_url(app):
    _get_geocode.cache_clear()
    app.config.pop("NOMINATIM_USER_AGENT", None)
    try:
        with app.app_context():
            geocode = _get_geocode()
        user_agent = geocode.func.__self__.headers["User-Agent"]
        assert user_agent.startswith("Invenio RDM (CESNET flavour, ")
        assert app.config.get("SITE_UI_URL", "") in user_agent
    finally:
        _get_geocode.cache_clear()


def test_get_geocode_min_delay_seconds_is_configurable(app):
    _get_geocode.cache_clear()
    try:
        with app.app_context():
            geocode = _get_geocode()
        # set in the app_config fixture: keep well under Nominatim's usage
        # policy even if some test forgets to mock the geocoder out
        assert geocode.min_delay_seconds == app.config["NOMINATIM_MIN_DELAY_SECONDS"]
        assert geocode.min_delay_seconds >= 5
    finally:
        _get_geocode.cache_clear()


def test_get_geocode_is_cached_process_wide(app):
    _get_geocode.cache_clear()
    try:
        with app.app_context():
            first = _get_geocode()
            second = _get_geocode()
        assert first is second
    finally:
        _get_geocode.cache_clear()
