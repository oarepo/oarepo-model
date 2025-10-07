#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Data type registry for OARepo models.

This module provides the DataTypeRegistry class that manages registration and
loading of data types from various sources including entry points, YAML files,
and JSON files for use in OARepo models.
"""

from __future__ import annotations

import importlib.metadata
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterable

from .base import DataType
from .wrapped import WrappedDataType

log = logging.getLogger("oarepo_model")


class DataTypeRegistry:
    """Registry for types used in the model."""

    def __init__(self) -> None:
        """Initialize the data type registry."""
        self.types: dict[str, DataType] = {}

    def load_entry_points(self) -> None:
        """Load types from entry points."""
        for ep in importlib.metadata.entry_points(group="oarepo_model.datatypes"):
            self.add_types(ep.load())

    def add_types(self, type_dict: dict[str, Any]) -> None:
        """Add types to the registry from a dictionary.

        :param type_dict: A dictionary where keys are type names and values are either DataType
                         subclasses or dictionaries defining the type.
        """
        self._unwind_shortcuts_in_properties(type_dict)

        for type_name, type_cls_or_dict in type_dict.items():
            if isinstance(type_cls_or_dict, dict):
                self.register(
                    type_name,
                    WrappedDataType(self, type_name, type_cls_or_dict),
                )
            elif issubclass(type_cls_or_dict, DataType):
                self.register(type_name, type_cls_or_dict(self, type_name))
            else:
                raise TypeError(
                    f"Invalid type for {type_name}: {type_cls_or_dict}. Expected a dict or a subclass of DataType.",
                )

    def register(self, type_name: str, datatype: DataType) -> None:
        """Register a data type in the registry."""
        if type_name in self.types:
            log.warning("Type %s is already registered, overwriting.", type_name)
        self.types[type_name] = datatype

    def get_type(self, type_name_or_dict: str | dict[str, Any]) -> DataType:
        """Get a data type by its name.

        :param type_name: The name of the data type.
        :return: The data type instance.
        """
        if isinstance(type_name_or_dict, dict):
            if "type" in type_name_or_dict:
                type_name = type_name_or_dict["type"]
            elif "properties" in type_name_or_dict:
                type_name = "object"
            elif "items" in type_name_or_dict:
                type_name = "array"
            else:
                raise ValueError(f"Can not get type from {type_name_or_dict}")
        else:
            type_name = type_name_or_dict

        if type_name not in self.types:
            raise KeyError(f"Data type '{type_name}' is not registered.")
        return self.types[type_name]

    def items(self) -> Iterable[tuple[str, DataType]]:
        """Return the items of the 'types' dictionary.

        :return: key-value tuple pairs of the 'types' dictionary.
        """
        return self.types.items()

    def _unwind_shortcuts_in_properties(
        self,
        type_dict: dict[str, Any],
    ) -> dict[str, Any]:
        ret: dict[str, Any] = {}
        for k, v in type_dict.items():
            vv = v
            if k.endswith("[]"):
                vv = {"type": "array", "items": vv}
            vv = self._unwind_shortcuts(vv)
            ret[k] = vv
        return ret

    def _unwind_shortcuts(self, v: Any) -> Any:
        if not isinstance(v, dict):
            return v
        if "properties" in v:
            v["properties"] = self._unwind_shortcuts_in_properties(v["properties"])
        elif "items" in v:
            v["items"] = self._unwind_shortcuts(v["items"])
        return v


def from_json(file_name: str, origin: str | None = None) -> dict[str, Any]:
    """Load custom data types from JSON files.

    Supports two formats:
    - A list of objects, each with a 'name' field (converted into a dictionary keyed by 'name')
    - A dictionary of named objects directly

    If `origin` is provided, `file_name` is resolved relative to the directory of the origin file.
    Otherwise, it is resolved relative to the current working directory.

    :param file_name: Name of the JSON file containing the data type definitions.
    :param origin: Optional path to the file from which the load is being called (e.g., `__file__`),
                   used to resolve the relative path to `file_name`.
    :return: A callable that returns a dictionary of data types when called.
    :raises TypeError: If the loaded content is neither a list nor a dictionary.
    """
    path = Path(origin).parent / file_name if origin else Path.cwd() / file_name

    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return {item.pop("name"): item for item in raw}
    if isinstance(raw, dict):
        return raw
    raise TypeError(f"Expected dict or list, got {type(raw)}")  # pragma: no cover


def from_yaml(file_name: str, origin: str | None = None) -> dict[str, Any]:
    """Load custom data types from YAML files.

    Supports two formats:
    - A list of objects, each with a 'name' field (converted into a dictionary keyed by 'name')
    - A dictionary of named objects directly

    If `origin` is provided, `file_name` is resolved relative to the directory of the origin file.
    Otherwise, it is resolved relative to the current working directory.

    :param file_name: Name of the YAML file containing the data type definitions.
    :param origin: Optional path to the file from which the load is being called (e.g., `__file__`),
                   used to resolve the relative path to `file_name`.
    :return: A callable that returns a dictionary of data types when called.
    :raises TypeError: If the loaded content is neither a list nor a dictionary.
    """
    path = Path(origin).parent / file_name if origin else Path.cwd() / file_name

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return {item.pop("name"): item for item in raw}
    if isinstance(raw, dict):
        return raw
    raise TypeError(f"Expected dict or list, got {type(raw)}")  # pragma: no cover
