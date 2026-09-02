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
from oarepo_model.presets.records_resources.records.date_range_dumper_ext import (
    EDTFDateRangeDumperExt,
)


def test_records_preset_date_range_dumper():
    m = model(
        name="date_range_dumper_ext_test",
        version="1.0.0",
        presets=[records_preset],
        types=[
            {
                "Metadata": {
                    "properties": {
                        "dates": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "date": {"type": "edtf-date-or-interval"},
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
                                                "dates": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "date": {
                                                                "type": "edtf-date-or-interval",
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
    date_range_extensions = [ext for ext in m.record_dumper_extensions if isinstance(ext, EDTFDateRangeDumperExt)]

    assert len(date_range_extensions) == 1
    assert date_range_extensions[0].paths == [
        ["metadata", "dates", "[]", "date"],
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
    ]


def test_array_of_dates_gets_a_sibling_array_of_ranges():
    """An array of dates gets one `dates_range` sibling holding all their ranges."""
    data = {"metadata": {"dates": ["2020", "2021/2022"]}}
    dumper = EDTFDateRangeDumperExt([["metadata", "dates", "[]"]])

    result = dumper.dump(None, deepcopy(data))

    assert result["metadata"]["dates"] == ["2020", "2021/2022"]
    assert result["metadata"]["dates_range"] == [
        {"gte": "2020-01-01", "lte": "2020-12-31"},
        {"gte": "2021-01-01", "lte": "2022-12-31"},
    ]
    assert dumper.load(deepcopy(result), None) == data


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

    result = dumper.dump(None, deepcopy(data))

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

    loaded = dumper.load(deepcopy(result), None)
    assert loaded["metadata"]["dates"][0]["date"] == "2020-05-10"
    assert "date_range" not in loaded["metadata"]["dates"][0]
    assert loaded["metadata"]["related_resources"][0]["dates"][0]["date"] == "2020/2021"
    assert "date_range" not in loaded["metadata"]["related_resources"][0]["dates"][0]
    assert loaded["metadata"]["related_resources"][0]["events"][0]["dates"][0]["date"] == "1999/2000"
    assert "date_range" not in loaded["metadata"]["related_resources"][0]["events"][0]["dates"][0]
