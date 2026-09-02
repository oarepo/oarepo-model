#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Base class for dumper extensions that convert field values at model paths."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invenio_records.dumpers import SearchDumperExt

from oarepo_model.datatypes.base import ARRAY_ITEM_PATH

if TYPE_CHECKING:
    from collections.abc import Callable


class PathDumperExtBase(SearchDumperExt):
    """Dumper extension that converts field values found at a fixed set of model paths.

    Subclasses implement the actual value conversion by overriding
    ``_data_to_opensearch`` (applied on dump) and ``_data_from_opensearch``
    (applied on load). Both receive the container holding the value and the key
    to read and write it: a dict and a field name, or - when the model path ends
    with an array - the list and the item's index. They also receive the chain
    of ``(container, key)`` pairs leading up to that point, innermost last, so
    an array item can reach its parent dict - e.g. to write a sibling field
    that aggregates over the whole array.
    """

    def __init__(self, paths: list[list[str]]):
        """Initialize with model paths to the fields to convert."""
        super().__init__()
        self.paths = paths

    def dump(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        record: Any,
        data: dict[str, Any],
    ) -> dict[str, Any]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Convert fields into their search representation."""
        _ = record
        for path in self.paths:
            self._apply(data, path, self._data_to_opensearch, [])
        return data

    def load(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        data: dict[str, Any],
        record_cls: type,
    ) -> dict[str, Any]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Convert fields back from their search representation."""
        _ = record_cls
        for path in self.paths:
            self._apply(data, path, self._data_from_opensearch, [])
        return data

    def _apply(
        self,
        data: Any,
        path: list[str],
        converter: Callable[[Any, Any, list[tuple[Any, Any]]], None],
        parent_path: list[tuple[Any, Any]],
    ) -> None:
        """Apply the converter to all values matching a path."""
        if not path:
            return
        key = path[0]
        if key == ARRAY_ITEM_PATH:
            if not isinstance(data, list):
                return
            if len(path) > 1:
                for item in data:
                    self._apply(item, path[1:], converter, parent_path)
            else:
                # the path ends with an array, so every item of it is converted
                for index in range(len(data)):
                    self._convert(data, index, converter, parent_path)
            return
        if isinstance(data, dict) and key in data:
            if len(path) > 1:
                self._apply(data[key], path[1:], converter, [*parent_path, (data, key)])
            else:
                self._convert(data, key, converter, parent_path)

    def _convert(
        self,
        container: Any,
        key: Any,
        converter: Callable[[Any, Any, list[tuple[Any, Any]]], None],
        parent_path: list[tuple[Any, Any]],
    ) -> None:
        """Convert one value, leaving the ones that are not set alone."""
        if container[key] is not None:
            converter(container, key, parent_path)

    def _data_to_opensearch(self, data: Any, key: Any, parent_path: list[tuple[Any, Any]]) -> None:
        """Convert one field's value to its OpenSearch representation.

        This method must be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def _data_from_opensearch(self, data: Any, key: Any, parent_path: list[tuple[Any, Any]]) -> None:
        """Convert one field's value back from its OpenSearch representation.

        This method must be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")
