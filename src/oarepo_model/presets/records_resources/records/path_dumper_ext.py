# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Base class for dumper extensions that convert field values at model paths."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records.dumpers import SearchDumperExt

from oarepo_model.datatypes.base import ARRAY_ITEM_PATH

if TYPE_CHECKING:
    from collections.abc import Callable


class PathDumperExtBase(SearchDumperExt):
    """Dumper extension that converts field values found at a fixed set of model paths.

    Subclasses implement the actual value conversion by overriding
    ``_data_to_opensearch`` (applied on dump) and ``_data_from_opensearch``
    (applied on load).
    """

    def __init__(self, paths: list[list[str]]):
        """Initialize with model paths to the fields to convert."""
        super().__init__()
        self.paths = paths

    @override
    def dump(
        self,
        record: Any,
        data: dict[str, Any],
    ) -> None:
        """Convert fields into their search representation, mutating data in place."""
        _ = record
        for path in self.paths:
            self._apply(data, path, self._data_to_opensearch)

    @override
    def load(
        self,
        data: dict[str, Any],
        record_cls: type,
    ) -> None:
        """Convert fields back from their search representation, mutating data in place."""
        _ = record_cls
        for path in self.paths:
            self._apply(data, path, self._data_from_opensearch)

    def _apply(
        self,
        data: Any,
        path: list[str],
        converter: Callable[[dict[str, Any], str], None],
    ) -> None:
        """Apply the converter to all values matching a path."""
        if not path:
            return
        key = path[0]
        if key == ARRAY_ITEM_PATH:
            if isinstance(data, list):
                for item in data:
                    self._apply(item, path[1:], converter)
            return
        if not isinstance(data, dict) or key not in data:
            return
        if len(path) > 1:
            self._apply(data[key], path[1:], converter)
            return
        converter(data, key)

    def _data_to_opensearch(self, data: dict[str, Any], key: str) -> None:
        """Convert one field's value to its OpenSearch representation.

        This method must be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def _data_from_opensearch(self, data: dict[str, Any], key: str) -> None:
        """Convert one field's value back from its OpenSearch representation.

        This method must be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")
