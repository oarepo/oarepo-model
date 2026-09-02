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

from oarepo_model.presets.records_resources.services.records.params import spherical
from oarepo_model.presets.records_resources.services.records.params.spherical import (
    GeoBoundingBoxParam,
    GeoDistanceParam,
    _format_km,
    _get_geocode,
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


# --- geo_distance: place-name (Nominatim) resolution ---
#
# These mock the module-level _nominatim_geocode_point function rather than
# hitting the real OpenStreetMap Nominatim service, to keep the tests fast,
# offline and deterministic.

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


@pytest.mark.parametrize(
    "geocoder_error",
    [ValueError("Nowhereville"), GeocoderTimedOut("timed out")],
    ids=["not_found", "geocoder_error"],
)
def test_geo_distance_param_geocoding_failure_raises(monkeypatch, geocoder_error):
    def fail(_name: str) -> tuple[float, float]:
        raise geocoder_error

    monkeypatch.setattr(spherical, "_nominatim_geocode_point", fail)

    with pytest.raises(QuerystringValidationError):
        GeoDistanceParam(config=None).apply(
            None,
            Search(),
            {"geo_distance:metadata.location": ["[Prague, Czechia,50km]"]},
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
