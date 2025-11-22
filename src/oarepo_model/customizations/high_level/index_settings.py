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


class PatchIndexSettings(PatchJSONFile):
    """Customization to patch/modify index settings."""

    modifies = ("record-mapping",)

    def __init__(self, settings: dict[str, Any]):
        """Initialize the customization with settings to patch."""
        self._settings = settings
        super().__init__("record-mapping", self._add_to_mapping)

    def _add_to_mapping(self, previous_data: dict[str, Any]) -> dict[str, Any]:
        """Add default search fields to the record mapping."""
        settings = previous_data.setdefault("settings", {})
        for k, v in self._settings.items():
            if k in settings:
                if isinstance(settings[k], int) and isinstance(v, int):
                    settings[k] = max(settings[k], v)
                elif isinstance(settings[k], list) and isinstance(v, list):
                    settings[k] = list(set(settings[k]) | set(v))
                elif isinstance(settings[k], dict) and isinstance(v, dict):
                    settings[k].update(v)
                    settings[k] = {kk: vv for kk, vv in settings[k].items() if vv is not None}
                else:
                    settings[k] = v
            else:
                settings[k] = v
        return previous_data


class SetIndexTotalFieldsLimit(PatchIndexSettings):
    """Customization to set the index.mapping.total_fields.limit setting."""

    def __init__(self, limit: int):
        """Initialize the customization with the total fields limit."""
        super().__init__({"index.mapping.total_fields.limit": limit})


class SetIndexNestedFieldsLimit(PatchIndexSettings):
    """Customization to set the index.mapping.nested_fields.limit setting."""

    def __init__(self, limit: int):
        """Initialize the customization with the nested fields limit."""
        super().__init__({"index.mapping.nested_fields.limit": limit})
