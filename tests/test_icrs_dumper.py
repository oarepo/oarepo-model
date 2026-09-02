#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

from __future__ import annotations

from copy import deepcopy

from oarepo_model.api import model
from oarepo_model.presets.records_resources import records_preset
from oarepo_model.presets.records_resources.records.spherical_dumper_ext import (
    ICRSDumperExt,
    ICRSShapeDumperExt,
)


def test_records_preset_icrs_dumper():
    m = model(
        name="icrs_dumper_ext_test",
        version="1.0.0",
        presets=[records_preset],
        types=[
            {
                "Metadata": {
                    "properties": {
                        "locations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "position": {"type": "icrs"},
                                },
                            },
                        },
                        "related_resources": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "events": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "locations": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "position": {
                                                                "type": "icrs",
                                                            },
                                                        },
                                                    },
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        ],
        metadata_type="Metadata",
    )
    icrs_extensions = [ext for ext in m.record_dumper_extensions if isinstance(ext, ICRSDumperExt)]

    assert len(icrs_extensions) == 1
    assert icrs_extensions[0].paths == [
        ["metadata", "locations", "[]", "position"],
        [
            "metadata",
            "related_resources",
            "[]",
            "events",
            "[]",
            "locations",
            "[]",
            "position",
        ],
    ]


def test_dumps_and_loads_nested_icrs_paths():
    data = {
        "metadata": {
            "locations": [{"position": {"ra": 10.0, "dec": -30.0}}],
            "related_resources": [
                {
                    "events": [
                        {
                            "locations": [
                                {"position": {"ra": 350.0, "dec": 45.0}},
                                {"position": {"ra": 200.0, "dec": 0.0}},
                            ],
                        },
                    ],
                },
            ],
        },
    }
    dumper = ICRSDumperExt(
        [
            ["metadata", "locations", "[]", "position"],
            [
                "metadata",
                "related_resources",
                "[]",
                "events",
                "[]",
                "locations",
                "[]",
                "position",
            ],
        ],
    )

    result = dumper.dump(None, deepcopy(data))

    assert result["metadata"]["locations"][0]["position"] == {"lat": -30.0, "lon": 10.0}
    events = result["metadata"]["related_resources"][0]["events"][0]
    assert events["locations"][0]["position"] == {"lat": 45.0, "lon": -10.0}
    assert events["locations"][1]["position"] == {"lat": 0.0, "lon": -160.0}

    loaded = dumper.load(deepcopy(result), None)

    assert loaded["metadata"]["locations"][0]["position"] == {"ra": 10.0, "dec": -30.0}
    loaded_events = loaded["metadata"]["related_resources"][0]["events"][0]
    assert loaded_events["locations"][0]["position"] == {"ra": 350.0, "dec": 45.0}
    assert loaded_events["locations"][1]["position"] == {"ra": 200.0, "dec": 0.0}


def test_records_preset_icrs_shape_dumper():
    m = model(
        name="icrs_shape_dumper_ext_test",
        version="1.0.0",
        presets=[records_preset],
        types=[
            {
                "Metadata": {
                    "properties": {
                        "footprint": {"type": "icrs_shape"},
                        "observation": {
                            "type": "object",
                            "properties": {
                                "field": {"type": "icrs_shape"},
                            },
                        },
                        # an array of shapes: the trailing "[]" is dropped so the
                        # converter, which handles lists, can reach the values
                        "footprints": {
                            "type": "array",
                            "items": {"type": "icrs_shape"},
                        },
                        "position": {"type": "icrs"},
                    },
                },
            },
        ],
        metadata_type="Metadata",
    )
    shape_extensions = [ext for ext in m.record_dumper_extensions if isinstance(ext, ICRSShapeDumperExt)]

    assert len(shape_extensions) == 1
    assert shape_extensions[0].paths == [
        ["metadata", "footprint"],
        ["metadata", "observation", "field"],
        ["metadata", "footprints"],
    ]


def test_dumps_and_loads_icrs_shapes():
    data = {
        "metadata": {
            "footprint": "POLYGON ((350 -30, 200 0, 10 45, 350 -30))",
            "footprints": [
                "POINT (200 0)",
                {"type": "Point", "coordinates": [-160.0, 0.0]},
            ],
        },
    }
    dumper = ICRSShapeDumperExt([["metadata", "footprint"], ["metadata", "footprints"]])

    result = dumper.dump(None, deepcopy(data))

    assert result["metadata"]["footprint"] == {
        "type": "Polygon",
        "coordinates": (((-10.0, -30.0), (-160.0, 0.0), (10.0, 45.0), (-10.0, -30.0)),),
    }
    assert result["metadata"]["footprints"][0] == {"type": "Point", "coordinates": (-160.0, 0.0)}
    assert result["metadata"]["footprints"][1] == {"type": "Point", "coordinates": (-160.0, 0.0)}

    loaded = dumper.load(deepcopy(result), None)

    # WKT is indexed as GeoJSON, so the round trip keeps the geometry but not its text
    assert loaded["metadata"]["footprint"]["type"] == "Polygon"
    assert loaded["metadata"]["footprint"]["coordinates"] == (
        ((350.0, -30.0), (200.0, 0.0), (10.0, 45.0), (350.0, -30.0)),
    )
    assert loaded["metadata"]["footprints"][0] == {"type": "Point", "coordinates": (200.0, 0.0)}

    # a third (height) ordinate is dropped rather than breaking the dump,
    # OpenSearch's geo_shape field being two-dimensional
    dumped = dumper.dump(None, {"metadata": {"footprint": "POINT (200 30 500)"}})
    assert dumped["metadata"]["footprint"] == {"type": "Point", "coordinates": (-160.0, 30.0)}
