#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate record mapping json file."""

from __future__ import annotations

from typing import Any

from ..patch_json_file import PatchJSONFile


class AddDefaultSearchFields(PatchJSONFile):
    """Customization to set model's permission policy."""

    modifies = ("record-mapping",)

    def __init__(self, *search_fields: str):
        """Initialize the customization with search fields to add."""
        self._search_fields = search_fields
        super().__init__("record-mapping", self._add_to_mapping)

    def _add_to_mapping(self, previous_data: dict[str, Any]) -> dict[str, Any]:
        """Add default search fields to the record mapping."""
        settings = previous_data.setdefault("settings", {})
        index_settings = settings.setdefault("index", {})
        query_settings = index_settings.setdefault("query", {})
        query_settings["default_field"] = list(
            {x for x in query_settings.get("default_field", []) if x != "*"} | set(self._search_fields),
        )
        return previous_data
