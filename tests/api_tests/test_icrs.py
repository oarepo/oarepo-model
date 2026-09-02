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
from invenio_records_resources.services.errors import QuerystringValidationError
from invenio_search import current_search_client
from opensearch_dsl import Search

from oarepo_model.datatypes.spherical import ra_dec_to_lat_lon
from oarepo_model.presets.records_resources.services.records.params import spherical
from oarepo_model.presets.records_resources.services.records.params.spherical import (
    IcrsBoundingBoxParam,
    IcrsDistanceParam,
    IcrsShapeParam,
    _degrees_to_km,
)

# Origin used as the search point for the icrs_distance tests below.
ORIGIN_RA = 83.6
ORIGIN_DEC = 22.0


def _point_south_of_origin(deg: float) -> dict[str, float]:
    """Return a point ``deg`` degrees south of ORIGIN along the same right ascension.

    Along a fixed right ascension, moving declination by ``deg`` degrees is
    exactly a ``deg``-degree great-circle separation, so this gives an exact
    angular distance without relying on the code under test to compute it.
    """
    return {"ra": ORIGIN_RA, "dec": ORIGIN_DEC - deg}


def test_icrs_distance_param_filters_and_boosts_by_distance(
    app,
    icrs_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    service = icrs_model.proxies.current_service
    Record = icrs_model.Record

    near = service.create(
        identity_simple,
        {"metadata": {"title": "Near", "position": _point_south_of_origin(1)}},
    )
    mid = service.create(
        identity_simple,
        {"metadata": {"title": "Mid", "position": _point_south_of_origin(3)}},
    )
    far = service.create(
        identity_simple,
        {"metadata": {"title": "Far", "position": _point_south_of_origin(20)}},
    )

    Record.index.refresh()

    search_dsl = service.create_search(identity_simple, Record, service.config.search)
    search_dsl = IcrsDistanceParam(service.config.search).apply(
        identity_simple,
        search_dsl,
        {"icrs_distance:metadata.position": [f"[{ORIGIN_RA},{ORIGIN_DEC},5]"]},
    )
    result = search_dsl.execute()

    hit_ids = [hit.id for hit in result]
    assert set(hit_ids) == {near.id, mid.id}
    assert far.id not in hit_ids

    # the closer record must score higher due to the distance_feature boost
    assert hit_ids.index(near.id) < hit_ids.index(mid.id)


def test_icrs_distance_param_via_service_search(
    app,
    icrs_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    """Exercise the full service.search() flow, as a real request would."""
    service = icrs_model.proxies.current_service
    Record = icrs_model.Record

    near = service.create(
        identity_simple,
        {"metadata": {"title": "Near", "position": _point_south_of_origin(1)}},
    )
    far = service.create(
        identity_simple,
        {"metadata": {"title": "Far", "position": _point_south_of_origin(20)}},
    )
    Record.index.refresh()

    result = service.search(
        identity_simple,
        facets={"icrs_distance:metadata.position": [f"[{ORIGIN_RA},{ORIGIN_DEC},5]"]},
    )

    hit_ids = {hit["id"] for hit in result.hits}
    assert hit_ids == {near.id}
    assert far.id not in hit_ids


def test_icrs_distance_param_removes_key_from_params():
    params = {"icrs_distance:metadata.position": ["[1,2,5]"], "other": ["x"]}

    IcrsDistanceParam(config=None).apply(None, Search(), params)

    assert params == {"other": ["x"]}


def test_icrs_distance_param_removes_key_from_facets_bucket():
    params = {"facets": {"icrs_distance:metadata.position": ["[1,2,5]"], "other": ["x"]}}

    IcrsDistanceParam(config=None).apply(None, Search(), params)

    assert params == {"facets": {"other": ["x"]}}


def test_icrs_distance_param_invalid_value_raises():
    with pytest.raises(QuerystringValidationError):
        IcrsDistanceParam(config=None).apply(
            None,
            Search(),
            {"icrs_distance:metadata.position": ["not-a-point"]},
        )


def test_icrs_distance_param_rejects_unit_suffix():
    """Unlike geo_distance:, the distance here is always in degrees, no unit."""
    with pytest.raises(QuerystringValidationError):
        IcrsDistanceParam(config=None).apply(
            None,
            Search(),
            {"icrs_distance:metadata.position": ["[1,2,5km]"]},
        )


def test_icrs_distance_param_converts_ra_dec_and_degrees():
    search = IcrsDistanceParam(config=None).apply(
        None,
        Search(),
        {"icrs_distance:metadata.position": [f"[{ORIGIN_RA},{ORIGIN_DEC},5]"]},
    )

    geo_distance = search.to_dict()["query"]["bool"]["filter"][0]["geo_distance"]
    lat, lon = ra_dec_to_lat_lon(ORIGIN_RA, ORIGIN_DEC)
    assert geo_distance["metadata.position"] == {"lat": lat, "lon": lon}
    assert geo_distance["distance"] == "555.975km"


# A box in ICRS right ascension/declination, spanning ra: 80-90, dec: 20-25.
BBOX_RA1, BBOX_DEC1 = 80.0, 20.0
BBOX_RA2, BBOX_DEC2 = 90.0, 25.0
BBOX_VALUE = f"[{BBOX_RA1},{BBOX_DEC1},{BBOX_RA2},{BBOX_DEC2}]"


def test_icrs_bounding_box_param_filters_and_boosts_by_distance(
    app,
    icrs_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    service = icrs_model.proxies.current_service
    Record = icrs_model.Record

    center = service.create(
        identity_simple,
        {"metadata": {"title": "Center", "position": {"ra": 85.0, "dec": 22.5}}},
    )
    corner = service.create(
        identity_simple,
        {"metadata": {"title": "Corner", "position": {"ra": 81.0, "dec": 20.5}}},
    )
    outside = service.create(
        identity_simple,
        {"metadata": {"title": "Outside", "position": {"ra": 85.0, "dec": 60.0}}},
    )

    Record.index.refresh()

    search_dsl = service.create_search(identity_simple, Record, service.config.search)
    search_dsl = IcrsBoundingBoxParam(service.config.search).apply(
        identity_simple,
        search_dsl,
        {"icrs_bounding_box:metadata.position": [BBOX_VALUE]},
    )
    result = search_dsl.execute()

    hit_ids = [hit.id for hit in result]
    assert set(hit_ids) == {center.id, corner.id}
    assert outside.id not in hit_ids

    # the record closer to the box's center must score higher
    assert hit_ids.index(center.id) < hit_ids.index(corner.id)


def test_icrs_bounding_box_param_via_service_search(
    app,
    icrs_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    service = icrs_model.proxies.current_service
    Record = icrs_model.Record

    inside = service.create(
        identity_simple,
        {"metadata": {"title": "Inside", "position": {"ra": 85.0, "dec": 22.5}}},
    )
    outside = service.create(
        identity_simple,
        {"metadata": {"title": "Outside", "position": {"ra": 85.0, "dec": 60.0}}},
    )
    Record.index.refresh()

    result = service.search(
        identity_simple,
        facets={"icrs_bounding_box:metadata.position": [BBOX_VALUE]},
    )

    hit_ids = {hit["id"] for hit in result.hits}
    assert hit_ids == {inside.id}
    assert outside.id not in hit_ids


def test_icrs_bounding_box_param_removes_key_from_params():
    params = {"icrs_bounding_box:metadata.position": ["[1,1,0,2]"], "other": ["x"]}

    IcrsBoundingBoxParam(config=None).apply(None, Search(), params)

    assert params == {"other": ["x"]}


def test_icrs_bounding_box_param_invalid_value_raises():
    with pytest.raises(QuerystringValidationError):
        IcrsBoundingBoxParam(config=None).apply(
            None,
            Search(),
            {"icrs_bounding_box:metadata.position": ["not-a-box"]},
        )


def test_icrs_bounding_box_param_converts_ra_dec_to_lat_lon():
    search = IcrsBoundingBoxParam(config=None).apply(
        None,
        Search(),
        {"icrs_bounding_box:metadata.position": [BBOX_VALUE]},
    )

    box = search.to_dict()["query"]["bool"]["filter"][0]["geo_bounding_box"]["metadata.position"]
    lat1, lon1 = ra_dec_to_lat_lon(BBOX_RA1, BBOX_DEC1)
    lat2, lon2 = ra_dec_to_lat_lon(BBOX_RA2, BBOX_DEC2)
    assert box == {
        "top_left": {"lat": max(lat1, lat2), "lon": min(lon1, lon2)},
        "bottom_right": {"lat": min(lat1, lat2), "lon": max(lon1, lon2)},
    }


GEO_SHAPE_POLYGON_WKT = (
    f"POLYGON (({BBOX_RA1} {BBOX_DEC1}, {BBOX_RA2} {BBOX_DEC1}, "
    f"{BBOX_RA2} {BBOX_DEC2}, {BBOX_RA1} {BBOX_DEC2}, {BBOX_RA1} {BBOX_DEC1}))"
)


def test_icrs_shape_param_filters_records(
    app,
    icrs_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    service = icrs_model.proxies.current_service
    Record = icrs_model.Record

    inside = service.create(
        identity_simple,
        {"metadata": {"title": "Inside", "position": {"ra": 85.0, "dec": 22.5}}},
    )
    outside = service.create(
        identity_simple,
        {"metadata": {"title": "Outside", "position": {"ra": 85.0, "dec": 60.0}}},
    )
    Record.index.refresh()

    search_dsl = service.create_search(identity_simple, Record, service.config.search)
    # no explicit operation: defaults to INTERSECTS, the only relation
    # OpenSearch allows against a geo_point-mapped field
    search_dsl = IcrsShapeParam(service.config.search).apply(
        identity_simple,
        search_dsl,
        {"icrs_shape:metadata.position": [GEO_SHAPE_POLYGON_WKT]},
    )
    result = search_dsl.execute()

    hit_ids = {hit.id for hit in result}
    assert hit_ids == {inside.id}
    assert outside.id not in hit_ids


def test_icrs_shape_param_via_service_search(
    app,
    icrs_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    service = icrs_model.proxies.current_service
    Record = icrs_model.Record

    inside = service.create(
        identity_simple,
        {"metadata": {"title": "Inside", "position": {"ra": 85.0, "dec": 22.5}}},
    )
    outside = service.create(
        identity_simple,
        {"metadata": {"title": "Outside", "position": {"ra": 85.0, "dec": 60.0}}},
    )
    Record.index.refresh()

    result = service.search(
        identity_simple,
        facets={"icrs_shape:metadata.position": [f"INTERSECTS {GEO_SHAPE_POLYGON_WKT}"]},
    )

    hit_ids = {hit["id"] for hit in result.hits}
    assert hit_ids == {inside.id}
    assert outside.id not in hit_ids


def test_icrs_shape_param_removes_key_from_params():
    params = {"icrs_shape:metadata.position": ["POINT (14.5 50.0)"], "other": ["x"]}

    IcrsShapeParam(config=None).apply(None, Search(), params)

    assert params == {"other": ["x"]}


def test_icrs_shape_param_invalid_value_raises():
    with pytest.raises(QuerystringValidationError):
        IcrsShapeParam(config=None).apply(
            None,
            Search(),
            {"icrs_shape:metadata.position": ["not a shape"]},
        )


def test_icrs_shape_param_converts_ra_dec_coordinates():
    search = IcrsShapeParam(config=None).apply(
        None,
        Search(),
        {"icrs_shape:metadata.position": ["POINT (83.6 22.0)"]},
    )

    shape_query = search.to_dict()["query"]["bool"]["filter"][0]["geo_shape"]["metadata.position"]
    lat, lon = ra_dec_to_lat_lon(83.6, 22.0)
    assert shape_query == {
        "shape": {"type": "Point", "coordinates": (lon, lat)},
        "relation": "intersects",
    }


def test_ra_dec_to_lat_lon():
    # dec becomes lat directly; ra is wrapped into [-180, 180) like ICRSDumperExt does
    assert ra_dec_to_lat_lon(10.0, -30.0) == (-30.0, 10.0)
    assert ra_dec_to_lat_lon(350.0, 45.0) == (45.0, -10.0)


def test_degrees_to_km_matches_earth_geo_distance_conversion():
    # 1 degree of great-circle angle is ~111.19 km on a sphere with earth's
    # mean radius - the same conversion geo_distance: relies on implicitly.
    assert _degrees_to_km(1) == pytest.approx(111.19, abs=0.05)


def test_icrs_shape_param_never_geocodes(monkeypatch):
    """ra/dec coordinates aren't Earth place names.

    geo_shape: falls back to geocoding non-WKT values as place names, but
    icrs_shape: must not: it should raise the ordinary invalid-WKT error
    instead of asking Nominatim to resolve celestial WKT-ish garbage.
    """

    def fail(_name: str) -> dict:
        raise AssertionError("icrs_shape: must never attempt geocoding")

    monkeypatch.setattr(spherical, "_nominatim_geocode_shape", fail)

    with pytest.raises(QuerystringValidationError):
        IcrsShapeParam(config=None).apply(
            None,
            Search(),
            {"icrs_shape:metadata.position": ["not a shape"]},
        )


#: A footprint around 3C 273 (ra ~187, dec ~2), its center as GeoJSON, and a
#: footprint far away from it. The right ascension is deliberately above 180:
#: that is the half of the sky where the ra -> lon conversion is not an identity,
#: so the indexed coordinates show whether ICRSShapeDumperExt ran.
NEAR_FOOTPRINT_WKT = "POLYGON ((187 2, 188 2, 188 3, 187 3, 187 2))"
NEAR_FOOTPRINT_CENTER_GEOJSON = {"type": "Point", "coordinates": [187.5, 2.5]}
FAR_FOOTPRINT_WKT = "POLYGON ((10 2, 11 2, 11 3, 10 3, 10 2))"


def test_icrs_shape_field_is_indexed_as_converted_geojson(
    app,
    icrs_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    """An icrs_shape field is indexed as GeoJSON lon/lat, WKT or GeoJSON input alike.

    The _source check is what pins the conversion: OpenSearch wraps a longitude
    of 187 to -173 itself, so a geo query alone cannot tell a converted shape
    from an unconverted one. Asserting the indexed document can.
    """
    service = icrs_model.proxies.current_service
    Record = icrs_model.Record

    wkt = service.create(
        identity_simple,
        {"metadata": {"title": "WKT", "footprint": NEAR_FOOTPRINT_WKT}},
    )
    geojson = service.create(
        identity_simple,
        {
            "metadata": {
                "title": "GeoJSON",
                "footprint": NEAR_FOOTPRINT_CENTER_GEOJSON,
            },
        },
    )
    service.create(
        identity_simple,
        {"metadata": {"title": "Far", "footprint": FAR_FOOTPRINT_WKT}},
    )
    Record.index.refresh()

    docs = current_search_client.search(
        index=Record.index._name,  # noqa: SLF001 - the index alias is only exposed privately
        body={"query": {"match_all": {}}},
    )
    indexed = {
        hit["_source"]["metadata"]["title"]: hit["_source"]["metadata"]["footprint"] for hit in docs["hits"]["hits"]
    }

    # WKT becomes GeoJSON, and ra 187/188 land at lon -173/-172
    assert indexed["WKT"] == {
        "type": "Polygon",
        "coordinates": [
            [[-173.0, 2.0], [-172.0, 2.0], [-172.0, 3.0], [-173.0, 3.0], [-173.0, 2.0]],
        ],
    }
    assert indexed["GeoJSON"] == {"type": "Point", "coordinates": [-172.5, 2.5]}

    # indexed geometrically, not just stored: queryable by icrs_shape:
    result = service.search(
        identity_simple,
        facets={"icrs_shape:metadata.footprint": [NEAR_FOOTPRINT_WKT]},
    )
    assert {hit["id"] for hit in result.hits} == {wkt.id, geojson.id}
