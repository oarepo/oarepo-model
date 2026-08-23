#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Shared helpers for resolving and walking a model's data type tree."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .collections import ObjectDataType

if TYPE_CHECKING:
    from collections.abc import Callable

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel

    from .base import DataType


def resolve_schema_type(
    builder: InvenioModelBuilder,
    schema_type: Any,
) -> tuple[DataType, dict[str, Any]]:
    """Resolve a schema type to its data type and element dict.

    ``schema_type`` may be a registered type name, an inline schema dict, or
    an already-instantiated :class:`ObjectDataType`.
    """
    if isinstance(schema_type, (str, dict)):
        datatype = builder.type_registry.get_type(schema_type)
        element = {} if isinstance(schema_type, str) else schema_type
        return datatype, element
    if isinstance(schema_type, ObjectDataType):
        return schema_type, {}
    raise TypeError(
        f"Invalid schema type: {schema_type}. Expected str, dict or None.",
    )


def get_model_nodes(
    builder: InvenioModelBuilder,
    model: InvenioModel,
    filter_func: Callable[[DataType], bool] | None = None,
    *,
    unique: bool = False,
) -> list[tuple[DataType, list[str]]]:
    """Return all visited data type nodes from the model.

    Polymorphic fields visit each ``oneof`` variant with the same path, so the
    same ``(datatype, path)`` pair can occur more than once (e.g. when two
    variants have a same-named field of the same type). Pass ``unique=True``
    to keep only the first node seen for each path.
    """
    nodes: list[tuple[DataType, list[str]]] = []
    seen: set[tuple[str, ...]] = set()

    def collect(datatype: DataType, path: list[str], element: dict[str, Any]) -> None:
        _ = element
        if filter_func is not None and not filter_func(datatype):
            return
        if unique:
            path_key = tuple(path)
            if path_key in seen:
                return
            seen.add(path_key)
        nodes.append((datatype, path))

    if model.record_type is not None:
        visit_schema(builder, model.record_type, [], collect)
    if model.metadata_type is not None:
        visit_schema(builder, model.metadata_type, ["metadata"], collect)
    return nodes


def node_type_filter(dt: type[DataType]) -> Callable[[DataType], bool]:
    """Return a filter function that checks if a data type is of the given type."""

    def _filter(datatype: DataType) -> bool:
        return isinstance(datatype, dt)

    return _filter


def visit_schema(
    builder: InvenioModelBuilder,
    schema_type: Any,
    path: list[str],
    visitor: Callable[[DataType, list[str], dict[str, Any]], None],
) -> None:
    """Visit one model schema tree."""
    datatype, element = resolve_schema_type(builder, schema_type)
    datatype.visit(element, path, visitor)
