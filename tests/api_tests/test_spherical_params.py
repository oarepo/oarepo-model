# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Contract shared by every _PrefixedGeoParam subclass.

Coordinate-system specific behaviour (axis order, wrap-around, geocoding, real
search) is tested in test_geo_point.py, test_geo_shape.py and test_icrs.py.
"""

from __future__ import annotations

import pytest
from invenio_records_resources.services.errors import QuerystringValidationError
from opensearch_dsl import Search

from oarepo_model.presets.records_resources.services.records.params.spherical import (
    GeoBoundingBoxParam,
    GeoDistanceParam,
    GeoShapeParam,
    IcrsBoundingBoxParam,
    IcrsDistanceParam,
    IcrsShapeParam,
)

PARAMS = pytest.mark.parametrize(
    ("param_class", "key", "valid", "invalid"),
    [
        (GeoDistanceParam, "geo_distance:metadata.location", "[14.4,50.0,10km]", "not-a-point"),
        (GeoBoundingBoxParam, "geo_bounding_box:metadata.location", "[0,1,1,2]", "not-a-box"),
        # plain text is a place name for geo_shape, so only malformed WKT is invalid
        (GeoShapeParam, "geo_shape:metadata.location", "POINT (14.5 50.0)", "POINT (abc)"),
        (IcrsDistanceParam, "icrs_distance:metadata.position", "[1,2,5]", "not-a-point"),
        (IcrsBoundingBoxParam, "icrs_bounding_box:metadata.position", "[1,1,0,2]", "not-a-box"),
        (IcrsShapeParam, "icrs_shape:metadata.position", "POINT (14.5 50.0)", "not a shape"),
    ],
    ids=["GeoDistance", "GeoBoundingBox", "GeoShape", "IcrsDistance", "IcrsBoundingBox", "IcrsShape"],
)


@PARAMS
def test_removes_key_from_params(param_class, key, valid, invalid):
    params = {key: [valid], "other": ["x"]}

    param_class(config=None).apply(None, Search(), params)

    assert params == {"other": ["x"]}


@PARAMS
def test_removes_key_from_facets_bucket(param_class, key, valid, invalid):
    """Must also handle the key nested in params["facets"].

    That's where the default SearchRequestArgsSchema puts unrecognized
    query-string keys for real requests.
    """
    params = {"facets": {key: [valid], "other": ["x"]}}

    param_class(config=None).apply(None, Search(), params)

    assert params == {"facets": {"other": ["x"]}}


@PARAMS
def test_invalid_value_raises(param_class, key, valid, invalid):
    with pytest.raises(QuerystringValidationError):
        param_class(config=None).apply(None, Search(), {key: [invalid]})
