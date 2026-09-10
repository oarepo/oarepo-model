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
from marshmallow.exceptions import ValidationError
from opensearch_dsl import Search
from opensearchpy.exceptions import RequestError

from oarepo_model.presets.records_resources.services.records.params import spherical
from oarepo_model.presets.records_resources.services.records.params.spherical import GeoShapeParam

# A ~1x1 degree box roughly covering Prague. lat: 49.5-50.5, lon: 14.0-15.0.
GEO_SHAPE_POLYGON_WKT = "POLYGON ((14.0 49.5, 15.0 49.5, 15.0 50.5, 14.0 50.5, 14.0 49.5))"

PRAGUE_LAT, PRAGUE_LON = 50.0755, 14.4378


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


# --- the geo_shape field itself: every supported geometry, in both forms ---

#: Every geometry type an OpenSearch geo_shape field understands, as WKT and as a
#: GeoJSON object. All of them lie inside GEO_SHAPE_POLYGON_WKT, so one and the
#: same query polygon must find every one of them.
#:
#: MULTIPOINT deliberately uses the 'MULTIPOINT (1 2, 3 4)' form: OpenSearch's
#: WKT parser rejects the parenthesised ISO form that shapely itself emits, and
#: the field is mapped with ignore_malformed, so such a shape would be stored and
#: silently left out of the geo index.
GEO_SHAPES = [
    ("wkt-point", "POINT (14.5 50.0)"),
    ("wkt-multipoint", "MULTIPOINT (14.4 50.0, 14.6 50.0)"),
    ("wkt-linestring", "LINESTRING (14.2 49.7, 14.8 50.3)"),
    ("wkt-multilinestring", "MULTILINESTRING ((14.2 49.7, 14.5 50.0), (14.5 50.0, 14.8 50.3))"),
    ("wkt-polygon", "POLYGON ((14.4 49.9, 14.6 49.9, 14.6 50.1, 14.4 50.1, 14.4 49.9))"),
    ("wkt-multipolygon", "MULTIPOLYGON (((14.4 49.9, 14.6 49.9, 14.6 50.1, 14.4 49.9)))"),
    ("wkt-collection", "GEOMETRYCOLLECTION (POINT (14.5 50.0), LINESTRING (14.2 49.7, 14.8 50.3))"),
    ("geojson-point", {"type": "Point", "coordinates": [14.5, 50.0]}),
    ("geojson-multipoint", {"type": "MultiPoint", "coordinates": [[14.4, 50.0], [14.6, 50.0]]}),
    ("geojson-linestring", {"type": "LineString", "coordinates": [[14.2, 49.7], [14.8, 50.3]]}),
    (
        "geojson-multilinestring",
        {
            "type": "MultiLineString",
            "coordinates": [[[14.2, 49.7], [14.5, 50.0]], [[14.5, 50.0], [14.8, 50.3]]],
        },
    ),
    (
        "geojson-polygon",
        {
            "type": "Polygon",
            "coordinates": [[[14.4, 49.9], [14.6, 49.9], [14.6, 50.1], [14.4, 50.1], [14.4, 49.9]]],
        },
    ),
    (
        "geojson-multipolygon",
        {"type": "MultiPolygon", "coordinates": [[[[14.4, 49.9], [14.6, 49.9], [14.6, 50.1], [14.4, 49.9]]]]},
    ),
    (
        "geojson-collection",
        {
            "type": "GeometryCollection",
            "geometries": [
                {"type": "Point", "coordinates": [14.5, 50.0]},
                {"type": "LineString", "coordinates": [[14.2, 49.7], [14.8, 50.3]]},
            ],
        },
    ),
]

#: A point in the Atlantic, for the negative half of the queries below.
FAR_SHAPE_WKT = "POINT (0.5 0.5)"
FAR_POLYGON_WKT = "POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))"

#: GEO_SHAPES plus WKT that validates and is stored verbatim, but that OpenSearch
#: cannot parse geometrically (an unclosed 3-point ring needs 'at least 4 polygon
#: points'), or parses differently than written (a third ordinate is dropped).
#: Stored as sent, never geo-queried, so they must not join GEO_SHAPES.
STORED_SHAPES = [
    *GEO_SHAPES,
    ("wkt-unclosed-ring", "POLYGON ((0 0, 1 1, 0 0))"),
    ("wkt-third-ordinate", "POINT (14.5 50.0 100)"),
]


def _shape_hit_ids(geo_model, identity_simple, query_wkt) -> set[str]:
    """Ids of the records whose metadata.shape intersects the given WKT."""
    result = geo_model.proxies.current_service.search(
        identity_simple,
        facets={"geo_shape:metadata.shape": [query_wkt]},
    )
    return {hit["id"] for hit in result.hits}


def test_geo_shape_field_stores_every_shape_verbatim(
    app,
    geo_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    """Every shape is stored exactly as sent, WKT or GeoJSON alike.

    Reading the record back runs the field's load and dump, so this is also the
    round-trip proof that the Raw field neither parses nor reformats a value.
    Round-tripping doesn't depend on whether a shape indexes correctly, so all of
    them go into one record's array field instead of one record each - a failure
    still points at the exact offending shape via the list diff. Whether each
    shape actually indexes is a separate concern, covered one at a time by
    test_geo_shape_field_searches_every_supported_shape below.
    """
    service = geo_model.proxies.current_service
    shapes = [shape for _, shape in STORED_SHAPES]

    created = service.create(identity_simple, {"metadata": {"title": "Shapes", "shapes": shapes}})

    assert service.read(identity_simple, created.id).data["metadata"]["shapes"] == shapes


@pytest.mark.parametrize("shape", [s for _, s in GEO_SHAPES], ids=[name for name, _ in GEO_SHAPES])
def test_geo_shape_field_searches_every_supported_shape(
    app,
    geo_model,
    identity_simple,
    search,
    search_clear,
    location,
    shape,
):
    """Every geometry must be geo-queryable, not merely stored.

    The field is mapped with ignore_malformed, so a shape OpenSearch cannot
    parse is kept in _source but dropped from the geo index without any error.
    Only querying proves it really was indexed geometrically.
    """
    service = geo_model.proxies.current_service
    Record = geo_model.Record

    here = service.create(identity_simple, {"metadata": {"title": "Here", "shape": shape}})
    far = service.create(identity_simple, {"metadata": {"title": "Far", "shape": FAR_SHAPE_WKT}})
    Record.index.refresh()

    assert _shape_hit_ids(geo_model, identity_simple, GEO_SHAPE_POLYGON_WKT) == {here.id}
    assert _shape_hit_ids(geo_model, identity_simple, FAR_POLYGON_WKT) == {far.id}


#: Shapes a geo_shape field must refuse: PostGIS curve and surface geometries
#: OpenSearch has no notion of, its non-GeoJSON 'envelope'/BBOX extension, valid
#: GeoJSON that is not a geometry, and values that are not a shape at all.
UNSUPPORTED_GEO_SHAPES = [
    ("wkt-circularstring", "CIRCULARSTRING (14.4 49.9, 14.5 50.0, 14.6 49.9)"),
    ("wkt-triangle", "TRIANGLE ((14.4 49.9, 14.6 49.9, 14.6 50.1, 14.4 49.9))"),
    ("wkt-bbox", "BBOX (14.0, 15.0, 50.5, 49.5)"),
    ("geojson-envelope", {"type": "envelope", "coordinates": [[14.0, 50.5], [15.0, 49.5]]}),
    (
        "geojson-feature",
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [14.5, 50.0]}, "properties": {}},
    ),
    ("geojson-bogus-type", {"type": "Bogus", "coordinates": [14.5, 50.0]}),
    ("geojson-no-coordinates", {"type": "Point"}),
    ("not-a-shape", "not a geo shape at all"),
    ("number", 42),
]


@pytest.mark.parametrize(
    "shape", [s for _, s in UNSUPPORTED_GEO_SHAPES], ids=[name for name, _ in UNSUPPORTED_GEO_SHAPES]
)
def test_unsupported_geo_shapes(
    app,
    geo_model,
    identity_simple,
    search,
    search_clear,
    location,
    shape,
):
    """Unsupported shapes are a validation error, never an indexing failure.

    This is the service path: it proves the field is wired into the record schema
    and that a bad shape stops at validation instead of reaching OpenSearch, where
    the mapping's ignore_malformed would otherwise swallow it.
    """
    service = geo_model.proxies.current_service

    with pytest.raises(ValidationError):
        service.create(identity_simple, {"metadata": {"title": "Unsupported", "shape": shape}})


# --- geo_shape: place-name (Nominatim) resolution ---
#
# These mock the module-level _nominatim_geocode_shape function rather than
# hitting the real OpenStreetMap Nominatim service, to keep the tests fast,
# offline and deterministic.


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
