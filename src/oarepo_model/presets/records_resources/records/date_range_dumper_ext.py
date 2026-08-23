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
