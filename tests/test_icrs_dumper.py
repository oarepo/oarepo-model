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
