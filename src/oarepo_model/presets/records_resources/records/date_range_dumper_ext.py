#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Date-range dumper extensions generated from model data types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.records.dumpers.edtf import (  # pyright: ignore[reportAttributeAccessIssue]
    _format_date,  # pyright: ignore[reportAttributeAccessIssue]
    parse_edtf,  # pyright: ignore[reportAttributeAccessIssue]
)

from oarepo_model.customizations import AddToList, Customization
from oarepo_model.datatypes.date import EDTFDateOrIntervalDataType
from oarepo_model.datatypes.tree import get_model_nodes
from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.records.path_dumper_ext import PathDumperExtBase

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


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


class DateRangeDumperExtPreset(Preset):
    """Preset that adds date-range dumper extensions discovered from the model."""

    modifies = ("record_dumper_extensions",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        paths = [
            path
            for _datatype, path in get_model_nodes(
                builder,
                model,
                lambda datatype: isinstance(datatype, EDTFDateOrIntervalDataType),
                unique=True,
            )
        ]

        if paths:
            yield AddToList("record_dumper_extensions", EDTFDateRangeDumperExt(paths))
