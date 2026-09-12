# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from copy import deepcopy

import pytest

from oarepo_model.api import model
from oarepo_model.presets.records_resources import records_preset
from oarepo_model.presets.records_resources.records.date_range_dumper_ext import (
    EDTFDateRangeDumperExt,
)
from oarepo_model.presets.records_resources.records.spherical_dumper_ext import (
    ICRSDumperExt,
)


@pytest.mark.parametrize(
    ("name", "field_type", "array_name", "field_name", "extension_cls"),
    [
        ("icrs_dumper_ext_test", "icrs", "locations", "position", ICRSDumperExt),
        ("date_range_dumper_ext_test", "edtf-date-or-interval", "dates", "date", EDTFDateRangeDumperExt),
    ],
    ids=["icrs", "date_range"],
)
def test_records_preset_registers_dumper_extension_with_nested_paths(
    name, field_type, array_name, field_name, extension_cls
):
    m = model(
        name=name,
        version="1.0.0",
        presets=[records_preset],
        types=[
            {
                "Metadata": {
                    "properties": {
                        array_name: {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    field_name: {"type": field_type},
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
                                                array_name: {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            field_name: {
                                                                "type": field_type,
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
    extensions = [ext for ext in m.record_dumper_extensions if isinstance(ext, extension_cls)]

    assert len(extensions) == 1
    assert extensions[0].paths == [
        ["metadata", array_name, "[]", field_name],
        [
            "metadata",
            "related_resources",
            "[]",
            "events",
            "[]",
            array_name,
            "[]",
            field_name,
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

    result = deepcopy(data)
    dumper.dump(None, result)

    assert result["metadata"]["locations"][0]["position"] == {"lat": -30.0, "lon": 10.0}
    events = result["metadata"]["related_resources"][0]["events"][0]
    assert events["locations"][0]["position"] == {"lat": 45.0, "lon": -10.0}
    assert events["locations"][1]["position"] == {"lat": 0.0, "lon": -160.0}

    loaded = deepcopy(result)
    dumper.load(loaded, None)

    assert loaded["metadata"]["locations"][0]["position"] == {"ra": 10.0, "dec": -30.0}
    loaded_events = loaded["metadata"]["related_resources"][0]["events"][0]
    assert loaded_events["locations"][0]["position"] == {"ra": 350.0, "dec": 45.0}
    assert loaded_events["locations"][1]["position"] == {"ra": 200.0, "dec": 0.0}


def test_dumps_and_loads_nested_date_range_paths():
    data = {
        "metadata": {
            "dates": [{"date": "2020-05-10"}],
            "related_resources": [
                {
                    "dates": [
                        {"date": "2020/2021"},
                        {"date": "2024-02"},
                    ],
                    "events": [
                        {
                            "dates": [
                                {"date": "1999/2000"},
                            ],
                        },
                    ],
                },
            ],
        },
    }
    dumper = EDTFDateRangeDumperExt(
        [
            ["metadata", "dates", "[]", "date"],
            ["metadata", "related_resources", "[]", "dates", "[]", "date"],
            [
                "metadata",
                "related_resources",
                "[]",
                "events",
                "[]",
                "dates",
                "[]",
                "date",
            ],
        ],
    )

    result = deepcopy(data)
    dumper.dump(None, result)

    assert result["metadata"]["dates"][0]["date"] == "2020-05-10"
    assert result["metadata"]["dates"][0]["date_range"] == {
        "gte": "2020-05-10",
        "lte": "2020-05-10",
    }
    assert result["metadata"]["related_resources"][0]["dates"][0]["date"] == "2020/2021"
    assert result["metadata"]["related_resources"][0]["dates"][0]["date_range"] == {
        "gte": "2020-01-01",
        "lte": "2021-12-31",
    }
    assert result["metadata"]["related_resources"][0]["dates"][1]["date_range"] == {
        "gte": "2024-02-01",
        "lte": "2024-02-29",
    }
    assert result["metadata"]["related_resources"][0]["events"][0]["dates"][0]["date_range"] == {
        "gte": "1999-01-01",
        "lte": "2000-12-31",
    }

    loaded = deepcopy(result)
    dumper.load(loaded, None)
    assert loaded["metadata"]["dates"][0]["date"] == "2020-05-10"
    assert "date_range" not in loaded["metadata"]["dates"][0]
    assert loaded["metadata"]["related_resources"][0]["dates"][0]["date"] == "2020/2021"
    assert "date_range" not in loaded["metadata"]["related_resources"][0]["dates"][0]
    assert loaded["metadata"]["related_resources"][0]["events"][0]["dates"][0]["date"] == "1999/2000"
    assert "date_range" not in loaded["metadata"]["related_resources"][0]["events"][0]["dates"][0]
