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
        {"geo_distance:metadata.location": [f"[{ORIGIN_LON},{ORIGIN_LAT},50km]"]},
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
        facets={"geo_distance:metadata.location": [f"[{ORIGIN_LON},{ORIGIN_LAT},50km]"]},
    )

    hit_ids = {hit["id"] for hit in result.hits}
    assert hit_ids == {near.id}
    assert far.id not in hit_ids


def test_geo_distance_param_removes_key_from_params():
    params = {"geo_distance:metadata.location": ["[14.4,50.0,10km]"], "other": ["x"]}

    GeoDistanceParam(config=None).apply(None, Search(), params)

    assert params == {"other": ["x"]}


def test_geo_distance_param_removes_key_from_facets_bucket():
    """Must also handle geo_distance:<field> nested in params["facets"].

    That's where the default SearchRequestArgsSchema puts unrecognized
    query-string keys for real requests.
    """
    params = {"facets": {"geo_distance:metadata.location": ["[14.4,50.0,10km]"], "other": ["x"]}}

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


def _distance_query(value: str) -> dict:
    search = GeoDistanceParam(config=None).apply(
        None,
        Search(),
        {"geo_distance:metadata.location": [value]},
    )
    return search.to_dict()["query"]["bool"]


def test_geo_distance_param_follows_geojson_position_axis_order():
    """RFC 7946 Section 3.1.1 orders a position longitude first, latitude second.

    This is not the latitude-first order of a 'geo' URI, so the same two numbers
    the other tests use for Prague must describe another point when written the
    other way round.
    """
    query = _distance_query("[14.4,50.0,50km]")
    assert query["filter"][0]["geo_distance"] == {
        "distance": "50km",
        "metadata.location": {"lat": 50.0, "lon": 14.4},
    }
    # the boost has to use the same point as the filter, not its transpose
    assert query["must"][0]["distance_feature"]["origin"] == {"lat": 50.0, "lon": 14.4}

    # Read as [lon, lat] this is a point in the Indian Ocean, not Prague.
    query = _distance_query("[50.0,14.4,50km]")
    assert query["filter"][0]["geo_distance"]["metadata.location"] == {"lat": 14.4, "lon": 50.0}
    assert query["must"][0]["distance_feature"]["origin"] == {"lat": 14.4, "lon": 50.0}


def test_geo_distance_param_geocoded_point_is_not_transposed(monkeypatch):
    """The geocoder answers latitude first; the point must survive that."""
    monkeypatch.setattr(spherical, "_nominatim_geocode_point", lambda _name: (ORIGIN_LAT, ORIGIN_LON))

    query = _distance_query("[Prague, Czechia,50km]")
    assert query["filter"][0]["geo_distance"]["metadata.location"] == {
        "lat": ORIGIN_LAT,
        "lon": ORIGIN_LON,
    }
    assert query["must"][0]["distance_feature"]["origin"] == {"lat": ORIGIN_LAT, "lon": ORIGIN_LON}


# A ~1x1 degree box roughly covering Prague. lat: 49.5-50.5, lon: 14.0-15.0.
# Named by its compass sides, which are also its RFC 7946 GeoJSON bbox roles:
# the first corner is the southwesterly one, the second the northeasterly one,
# each given as longitude before latitude.
BBOX_SOUTH = 49.5
BBOX_WEST = 14.0
BBOX_NORTH = 50.5
BBOX_EAST = 15.0
BBOX_VALUE = f"[{BBOX_WEST},{BBOX_SOUTH},{BBOX_EAST},{BBOX_NORTH}]"


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
    params = {"geo_bounding_box:metadata.location": ["[0,1,1,2]"], "other": ["x"]}

    GeoBoundingBoxParam(config=None).apply(None, Search(), params)

    assert params == {"other": ["x"]}


def test_geo_bounding_box_param_removes_key_from_facets_bucket():
    """Must also handle geo_bounding_box:<field> nested in params["facets"]."""
    params = {"facets": {"geo_bounding_box:metadata.location": ["[0,1,1,2]"], "other": ["x"]}}

    GeoBoundingBoxParam(config=None).apply(None, Search(), params)

    assert params == {"facets": {"other": ["x"]}}


def test_geo_bounding_box_param_invalid_value_raises():
    with pytest.raises(QuerystringValidationError):
        GeoBoundingBoxParam(config=None).apply(
            None,
            Search(),
            {"geo_bounding_box:metadata.location": ["not-a-box"]},
        )


def _bbox_query(value: str) -> dict:
    """Build the bool query produced by a ``geo_bounding_box:<field>`` parameter."""
    search = GeoBoundingBoxParam(config=None).apply(
        None,
        Search(),
        {"geo_bounding_box:metadata.location": [value]},
    )
    return search.to_dict()["query"]["bool"]


def test_geo_bounding_box_param_ordered_corners():
    query = _bbox_query(BBOX_VALUE)

    assert query["filter"][0]["geo_bounding_box"]["metadata.location"] == {
        "top_left": {"lat": BBOX_NORTH, "lon": BBOX_WEST},
        "bottom_right": {"lat": BBOX_SOUTH, "lon": BBOX_EAST},
    }
    assert query["must"][0]["distance_feature"]["origin"] == {"lat": 50.0, "lon": 14.5}
    # the distance from the box's center to one of its corners
    assert query["must"][0]["distance_feature"]["pivot"] == "66.193km"


def test_geo_bounding_box_param_follows_geojson_bbox_axis_order():
    """RFC 7946 orders a bbox [west, south, east, north]: longitude first.

    The same four numbers the other tests use for Prague, written the
    latitude-first way instead, must therefore describe a different box.
    """
    assert _bbox_query("[14.0,49.5,15.0,50.5]")["filter"][0]["geo_bounding_box"]["metadata.location"] == {
        "top_left": {"lat": 50.5, "lon": 14.0},
        "bottom_right": {"lat": 49.5, "lon": 15.0},
    }
    # Read as [west, south, east, north] these are lon 49.5..50.5, lat 14..15.
    assert _bbox_query("[49.5,14.0,50.5,15.0]")["filter"][0]["geo_bounding_box"]["metadata.location"] == {
        "top_left": {"lat": 15.0, "lon": 49.5},
        "bottom_right": {"lat": 14.0, "lon": 50.5},
    }


def test_geo_bounding_box_param_requires_the_lower_latitude_first():
    """Reversed latitudes are not a synonym for the same box, they are an error."""
    value = f"[{BBOX_WEST},{BBOX_NORTH},{BBOX_EAST},{BBOX_SOUTH}]"

    with pytest.raises(QuerystringValidationError):
        GeoBoundingBoxParam(config=None).apply(
            None,
            Search(),
            {"geo_bounding_box:metadata.location": [value]},
        )


@pytest.mark.parametrize(
    ("value", "top_left", "bottom_right", "center"),
    [
        # Longitudes outside [-180, 180] are folded back into that range before
        # the box is built: 190 and 200 are the same meridians as -170 and -160.
        (
            "[190,49.5,200,50.5]",
            {"lat": 50.5, "lon": -170.0},
            {"lat": 49.5, "lon": -160.0},
            {"lat": 50.0, "lon": -165.0},
        ),
        # Latitude outside [-90, 90] is folded into range the same way: 370 and
        # 375 become 10 and 15, an ordinary ordered box.
        (
            "[14,370,15,375]",
            {"lat": 15.0, "lon": 14.0},
            {"lat": 10.0, "lon": 15.0},
            {"lat": 12.5, "lon": 14.5},
        ),
        # The range is half-open, so 180 folds to -180 rather than staying put:
        # the same meridian, written the way every other longitude is here. The
        # box it describes is still the 20 degrees east of 180, not the 340
        # degrees west of it.
        (
            "[180,49.5,200,50.5]",
            {"lat": 50.5, "lon": -180.0},
            {"lat": 49.5, "lon": -160.0},
            {"lat": 50.0, "lon": -170.0},
        ),
    ],
)
def test_geo_bounding_box_param_normalizes_out_of_range_coordinates(value, top_left, bottom_right, center):
    """Corners outside the accepted ranges are folded back into them."""
    query = _bbox_query(value)

    assert query["filter"][0]["geo_bounding_box"]["metadata.location"] == {
        "top_left": top_left,
        "bottom_right": bottom_right,
    }
    assert query["must"][0]["distance_feature"]["origin"] == center


@pytest.mark.parametrize(
    ("west", "east", "center_lon", "pivot"),
    [
        # Eastward from 170 through 180 to -170: 20 degrees wide, crosses the
        # antimeridian, so its center lies on the antimeridian.
        (170.0, -170.0, -180.0, "720.064km"),
        # Eastward from -170 through 0 to 170: the complementary box, 340
        # degrees wide and centered on the Greenwich meridian.
        (-170.0, 170.0, 0.0, "8910.214km"),
    ],
)
def test_geo_bounding_box_param_antimeridian(west, east, center_lon, pivot):
    value = f"[{west},{BBOX_SOUTH},{east},{BBOX_NORTH}]"
    query = _bbox_query(value)

    # A top_left lon greater than the bottom_right lon is how OpenSearch knows
    # that the box crosses the antimeridian.
    assert query["filter"][0]["geo_bounding_box"]["metadata.location"] == {
        "top_left": {"lat": BBOX_NORTH, "lon": west},
        "bottom_right": {"lat": BBOX_SOUTH, "lon": east},
    }
    feature = query["must"][0]["distance_feature"]
    assert feature["origin"] == {"lat": 50.0, "lon": center_lon}
    # each box's pivot follows its own width, not the short way round the globe
    assert feature["pivot"] == pivot


@pytest.mark.parametrize(
    ("value", "expected_titles"),
    [
        # The two narrow boxes on either side of 180 are one box here.
        ("[170.0,49.5,-170.0,50.5]", {"East of the line", "West of the line"}),
        # Its complement: everything the crossing box excludes.
        ("[-170.0,49.5,170.0,50.5]", {"Greenwich"}),
    ],
)
def test_geo_bounding_box_param_antimeridian_filters(
    app,
    geo_model,
    identity_simple,
    search,
    search_clear,
    location,
    value,
    expected_titles,
):
    """Both a crossing box and its complement really do filter as meant."""
    service = geo_model.proxies.current_service
    Record = geo_model.Record

    for title, lon in (("East of the line", 175.0), ("West of the line", -175.0), ("Greenwich", 0.0)):
        service.create(identity_simple, {"metadata": {"title": title, "location": {"lat": 50.0, "lon": lon}}})
    Record.index.refresh()

    search_dsl = GeoBoundingBoxParam(service.config.search).apply(
        identity_simple,
        service.create_search(identity_simple, Record, service.config.search),
        {"geo_bounding_box:metadata.location": [value]},
    )

    assert {hit.metadata.title for hit in search_dsl.execute()} == expected_titles


def test_geo_bounding_box_param_polar_cap():
    """RFC 7946 5.3 writes a box reaching a pole with the full longitude span.

    West and east then share a meridian once 180 folds to -180, which has to be
    read as the whole globe and not as a box of no width: OpenSearch rejects a
    zero-width one outright.
    """
    query = _bbox_query("[-180,80,180,90]")

    assert query["filter"][0]["geo_bounding_box"]["metadata.location"] == {
        "top_left": {"lat": 90.0, "lon": -180.0},
        "bottom_right": {"lat": 80.0, "lon": 180.0},
    }
    feature = query["must"][0]["distance_feature"]
    assert feature["origin"] == {"lat": 85.0, "lon": 0.0}
    # a quarter of the way round the world from the center to a corner
    assert feature["pivot"] == "1667.926km"


@pytest.mark.parametrize(
    ("value", "expected_titles"),
    [
        # The Arctic cap runs to the pole, exactly as RFC 7946 Section 5.3 has it.
        ("[-180,80,180,90]", {"In the Arctic", "At the pole"}),
        # Same cap without the poles: the subarctic point joins in.
        ("[-180,70,180,90]", {"In the Arctic", "At the pole", "Subarctic"}),
        # The whole world by its full span.
        ("[-180,-90,180,90]", {"In the Arctic", "At the pole", "Subarctic", "Temperate"}),
    ],
)
def test_geo_bounding_box_param_polar_cap_filters(
    app,
    geo_model,
    identity_simple,
    search,
    search_clear,
    location,
    value,
    expected_titles,
):
    """A box that reaches a pole selects the cap instead of erroring out."""
    service = geo_model.proxies.current_service
    Record = geo_model.Record

    for title, lat, lon in (
        ("At the pole", 89.0, 0.0),
        ("In the Arctic", 85.0, 100.0),
        ("Subarctic", 78.0, 15.0),
        ("Temperate", 50.0, 14.5),
    ):
        service.create(identity_simple, {"metadata": {"title": title, "location": {"lat": lat, "lon": lon}}})
    Record.index.refresh()

    search_dsl = GeoBoundingBoxParam(service.config.search).apply(
        identity_simple,
        service.create_search(identity_simple, Record, service.config.search),
        {"geo_bounding_box:metadata.location": [value]},
    )

    assert {hit.metadata.title for hit in search_dsl.execute()} == expected_titles


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
        raise AssertionError("should not geocode numeric lon/lat")

    monkeypatch.setattr(spherical, "_nominatim_geocode_point", fail)

    GeoDistanceParam(config=None).apply(
        None,
        Search(),
        {"geo_distance:metadata.location": ["[14.4,50.0,50km]"]},
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
