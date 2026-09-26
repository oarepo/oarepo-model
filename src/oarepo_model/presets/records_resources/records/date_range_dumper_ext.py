# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Date-range dumper extensions generated from model data types."""

from __future__ import annotations

from typing import Any

from invenio_rdm_records.records.dumpers.edtf import (
    _format_date,
    parse_edtf,
)

from oarepo_model.datatypes.date import EDTFDateOrIntervalDataType
from oarepo_model.presets.records_resources.records.path_dumper_ext import (
    PathDumperExtBase,
    PathDumperExtPreset,
)


def _edtf_to_range(value: str) -> dict[str, str]:
    """Convert one EDTF value to its `{gte, lte}` range representation."""
    parsed_date = parse_edtf(value)
    return {
        "gte": _format_date(parsed_date.lower_strict()),
        "lte": _format_date(parsed_date.upper_strict()),
    }


class EDTFDateRangeDumperExt(PathDumperExtBase):
    """Dump EDTF date-or-interval fields to sibling OpenSearch date_range fields."""

    def _data_to_opensearch(self, data: Any, key: Any, parent_path: list[tuple[Any, Any]]) -> None:
        """Dump one EDTF value to a sibling range field.

        A plain field gets its own `{key}_range` sibling. An item of an array
        of dates has no sibling of its own, so its range is appended to a
        `{field}_range` array on the array's parent instead - OpenSearch's
        date_range field accepts multiple ranges per field.
        """
        range_ = _edtf_to_range(data[key])
        if isinstance(data, dict):
            data[f"{key}_range"] = range_
        else:
            parent, parent_key = parent_path[-1]
            parent.setdefault(f"{parent_key}_range", []).append(range_)

    def _data_from_opensearch(self, data: Any, key: Any, parent_path: list[tuple[Any, Any]]) -> None:
        """Remove the generated range field."""
        if isinstance(data, dict):
            data.pop(f"{key}_range", None)
        else:
            parent, parent_key = parent_path[-1]
            parent.pop(f"{parent_key}_range", None)


class DateRangeDumperExtPreset(PathDumperExtPreset):
    """Preset that adds date-range dumper extensions discovered from the model."""

    datatype_class = EDTFDateOrIntervalDataType
    dumper_ext_class = EDTFDateRangeDumperExt
