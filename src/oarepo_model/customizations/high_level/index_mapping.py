#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to patch record mapping json file."""

from __future__ import annotations

from typing import Any, cast

from deepmerge import always_merger

from ..patch_json_file import PatchJSONFile


class PatchIndexMapping(PatchJSONFile):
    """Customization to patch/modify index mapping."""

    modifies = ("record-mapping",)

    def __init__(self, mapping: dict[str, Any]):
        """Initialize the customization with mapping to patch."""
        self._mapping = mapping
        super().__init__("record-mapping", self._add_to_mapping)

    def _add_to_mapping(self, previous_data: dict[str, Any]) -> dict[str, Any]:
        """Merge the provided mapping snippet into the mapping file."""
        mapping = previous_data.setdefault("mappings", {})
        # deep merge of mappings
        always_merger.merge(mapping, self._mapping)
        # remove None values
        recursively_remove_none(mapping)
        return previous_data


def recursively_remove_none(d: Any) -> None:
    """Recursively remove None values from dicts and lists."""
    if isinstance(d, dict):
        for k, v in list(d.items()):
            if v is None:
                del d[k]
            else:
                recursively_remove_none(v)
    elif isinstance(d, list):
        # iterate in reverse to safely remove items without affecting indices
        for idx, item in reversed(list(enumerate(d))):
            if item is None:
                del d[idx]
            else:
                recursively_remove_none(item)


class PatchIndexPropertyMapping(PatchIndexMapping):
    """Customization to patch/modify a specific property in index mapping."""

    def __init__(self, property_path: str, mapping: dict[str, Any] | None):
        """Initialize the customization with a property path and mapping snippet to patch."""
        parts = property_path.split(".")
        current = mapping
        for part in reversed(parts):
            current = {"properties": {part: current}}
        super().__init__(cast("dict", current))
