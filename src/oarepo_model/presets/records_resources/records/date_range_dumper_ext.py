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
from invenio_records.dumpers import SearchDumperExt

from oarepo_model.customizations import AddToList, Customization
from oarepo_model.datatypes.base import ARRAY_ITEM_PATH, DataType
from oarepo_model.datatypes.collections import ObjectDataType
from oarepo_model.datatypes.date import EDTFDateOrIntervalDataType
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class EDTFDateRangeDumperExt(SearchDumperExt):
    """Dump EDTF date-or-interval fields to sibling OpenSearch date_range fields."""

    def __init__(self, paths: list[list[str]]):
        """Initialize with model paths to EDTF date-or-interval fields."""
        super().__init__()
        self.paths = paths

    def dump(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        record: Any,
        data: dict[str, Any],
    ) -> dict[str, Any]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Dump date_range fields into the search representation."""
        _ = record
        for path in self.paths:
            self._apply(data, path, dump=True)
        return data

    def load(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        data: dict[str, Any],
        record_cls: type,
    ) -> dict[str, Any]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Remove generated date_range fields from the record representation."""
        _ = record_cls
        for path in self.paths:
            self._apply(data, path, dump=False)
        return data

    def _apply(self, data: Any, path: list[str], dump: bool) -> None:
        """Apply dump or load operation to all values matching a path."""
        if not path:
            return
        key = path[0]
        if key == ARRAY_ITEM_PATH:
            if isinstance(data, list):
                for item in data:
                    self._apply(item, path[1:], dump)
            return
        if not isinstance(data, dict) or key not in data:
            return
        if len(path) > 1:
            self._apply(data[key], path[1:], dump)
            return
        if dump:
            self._dump_value(data, key)
        else:
            data.pop(f"{key}_range", None)

    def _dump_value(self, data: dict[str, Any], key: str) -> None:
        """Dump one EDTF value to a sibling range field."""
        parsed_date = parse_edtf(data[key])
        data[f"{key}_range"] = {
            "gte": _format_date(parsed_date.lower_strict()),
            "lte": _format_date(parsed_date.upper_strict()),
        }


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
        paths = get_date_or_interval_paths(builder, model)
        if paths:
            yield AddToList("record_dumper_extensions", EDTFDateRangeDumperExt(paths))


def get_date_or_interval_paths(
    builder: InvenioModelBuilder,
    model: InvenioModel,
) -> list[list[str]]:
    """Collect paths to EDTF date-or-interval fields from the model."""
    paths: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for datatype, path in get_model_nodes(builder, model):
        if not isinstance(datatype, EDTFDateOrIntervalDataType):
            continue
        path_key = tuple(path)
        if path_key in seen:
            continue
        seen.add(path_key)
        paths.append(path)
    return paths


def get_model_nodes(builder: InvenioModelBuilder, model: InvenioModel) -> list[tuple[DataType, list[str]]]:
    """Return all visited data type nodes from the model."""
    nodes: list[tuple[DataType, list[str]]] = []

    def collect(datatype: DataType, path: list[str], element: dict[str, Any]) -> None:
        _ = element
        nodes.append((datatype, path))

    if model.record_type is not None:
        visit_schema(builder, model.record_type, [], collect)
    if model.metadata_type is not None:
        visit_schema(builder, model.metadata_type, ["metadata"], collect)
    return nodes


def visit_schema(
    builder: InvenioModelBuilder,
    schema_type: Any,
    path: list[str],
    visitor: Any,
) -> None:
    """Visit one model schema tree."""
    if isinstance(schema_type, (str, dict)):
        datatype = builder.type_registry.get_type(schema_type)
        datatype.visit({} if isinstance(schema_type, str) else schema_type, path, visitor)
    elif isinstance(schema_type, ObjectDataType):
        schema_type.visit({}, path, visitor)
    else:
        raise TypeError(
            f"Invalid schema type: {schema_type}. Expected str, dict or None.",
        )
