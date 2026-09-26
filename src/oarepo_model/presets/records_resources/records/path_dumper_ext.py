# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Base machinery for dumper extensions that convert field values at model paths."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, override

from invenio_records.dumpers import SearchDumperExt

from oarepo_model.customizations import AddToList, Customization
from oarepo_model.datatypes.base import ARRAY_ITEM_PATH
from oarepo_model.datatypes.tree import get_model_nodes
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.datatypes.base import DataType
    from oarepo_model.model import InvenioModel


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

    @override
    def dump(
        self,
        record: Any,
        data: dict[str, Any],
    ) -> None:
        """Convert fields into their search representation, mutating data in place."""
        _ = record
        for path in self.paths:
            self._apply(data, path, self._data_to_opensearch, [])

    @override
    def load(
        self,
        data: dict[str, Any],
        record_cls: type,
    ) -> None:
        """Convert fields back from their search representation, mutating data in place."""
        _ = record_cls
        for path in self.paths:
            self._apply(data, path, self._data_from_opensearch, [])

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


class PathDumperExtPreset(Preset):
    """Preset that adds a PathDumperExtBase for all fields of a given datatype."""

    modifies = ("record_dumper_extensions",)

    datatype_class: ClassVar[type[DataType]]
    dumper_ext_class: ClassVar[type[PathDumperExtBase]]

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
                lambda datatype: isinstance(datatype, self.datatype_class),
                unique=True,
            )
        ]

        if paths:
            yield AddToList("record_dumper_extensions", self.dumper_ext_class(paths))
