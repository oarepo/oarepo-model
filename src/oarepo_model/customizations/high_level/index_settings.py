# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Search index settings: ``PatchIndexSettings``, ``SetIndexTotalFieldsLimit``, ``SetIndexNestedFieldsLimit``.

- ``PatchIndexSettings(settings)`` - merges ``settings`` (analyzers, tokenizers,
  filters, ...) into the index settings. The merge is only one level deep: a
  second patch of the same top-level key (e.g. ``analysis``) replaces what the
  first one set, so keep all analysis settings in one call.
- ``SetIndexTotalFieldsLimit(limit)`` - maximum number of fields in the mapping;
  raise it for large metadata models.
- ``SetIndexNestedFieldsLimit(limit)`` - maximum number of ``nested`` fields.

Example (in ``model.py``):

```python
from oarepo_model.customizations import (
    PatchIndexSettings,
    SetIndexTotalFieldsLimit,
)

PatchIndexSettings(
    {
        "analysis": {
            "analyzer": {
                "asciifolded_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "asciifolding",
                    ],
                },
            },
        },
    }
)
SetIndexTotalFieldsLimit(5000)
```

See https://nrp-cz.github.io/docs/customize/model_backend/search#basic-search-customizations
"""

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
                    base = settings[k]
                    settings[k] = [*base, *(x for x in v if x not in base)]
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
