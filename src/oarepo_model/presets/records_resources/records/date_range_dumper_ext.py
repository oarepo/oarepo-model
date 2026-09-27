# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""EDTF dumper extensions generated from model data types."""

from __future__ import annotations

import re
from logging import getLogger
from typing import Any

from invenio_rdm_records.records.dumpers.edtf import (
    _format_date,
    parse_edtf,
)

from oarepo_model.datatypes.date import EDTFDateOrIntervalDataType, EDTFIntervalType, EDTFTimeDataType
from oarepo_model.presets.records_resources.records.path_dumper_ext import (
    PathDumperExtBase,
    PathDumperExtPreset,
)

_log = getLogger(__name__)

#: an EDTF datetime carries an explicit timezone offset iff it ends in one
_OFFSET_SUFFIX = re.compile(r"(Z|[+-]\d{2}:\d{2})$")


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

        A value that passed marshmallow validation but crashes the EDTF
        library's range conversion is skipped: the record stays in the index,
        merely without that one range, rather than failing the whole document.
        """
        try:
            range_ = _edtf_to_range(data[key])
        except Exception as error:  # noqa: BLE001
            _log.warning("Could not convert EDTF value %r to a date range, skipping: %s", data[key], error)
            return
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

    datatype_class = (EDTFDateOrIntervalDataType, EDTFIntervalType)
    dumper_ext_class = EDTFDateRangeDumperExt


class EDTFTimeDumperExt(PathDumperExtBase):
    """Dump naive EDTF datetimes as UTC: append ``Z`` when the offset is missing."""

    def _data_to_opensearch(self, data: Any, key: Any, parent_path: list[tuple[Any, Any]]) -> None:
        """Append ``Z`` to a datetime without an offset, so the mapping parses it."""
        _ = parent_path
        value = data[key]
        # the value passed EDTF validation: a 'T' marks a datetime, and one
        # without an offset suffix is naive
        if "T" in value and not _OFFSET_SUFFIX.search(value):
            data[key] = f"{value}Z"

    def _data_from_opensearch(self, data: Any, key: Any, parent_path: list[tuple[Any, Any]]) -> None:
        """Keep the indexed value: whether the offset was typed or appended is unrecoverable."""
        _, _, _ = data, key, parent_path


class EDTFTimeDumperExtPreset(PathDumperExtPreset):
    """Preset that appends ``Z`` to naive edtf-time datetimes when indexing."""

    datatype_class = EDTFTimeDataType
    dumper_ext_class = EDTFTimeDumperExt
