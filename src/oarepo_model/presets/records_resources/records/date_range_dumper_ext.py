# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
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


class EDTFDateRangeDumperExt(PathDumperExtBase):
    """Dump EDTF date-or-interval fields to sibling OpenSearch date_range fields."""

    def _data_to_opensearch(self, data: dict[str, Any], key: str) -> None:
        """Dump one EDTF value to a sibling range field."""
        parsed_date = parse_edtf(data[key])
        data[f"{key}_range"] = {
            "gte": _format_date(parsed_date.lower_strict()),
            "lte": _format_date(parsed_date.upper_strict()),
        }

    def _data_from_opensearch(self, data: dict[str, Any], key: str) -> None:
        """Remove the generated range field."""
        data.pop(f"{key}_range", None)


class DateRangeDumperExtPreset(PathDumperExtPreset):
    """Preset that adds date-range dumper extensions discovered from the model."""

    datatype_class = EDTFDateOrIntervalDataType
    dumper_ext_class = EDTFDateRangeDumperExt
