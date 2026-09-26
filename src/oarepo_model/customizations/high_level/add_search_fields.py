# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to generate record mapping json file."""

from __future__ import annotations

from .index_settings import PatchIndexSettings


class SetDefaultSearchFields(PatchIndexSettings):
    """Customization to specify a set of search fields."""

    modifies = ("record-mapping",)

    def __init__(self, *search_fields: str):
        """Initialize the customization with search fields to add."""
        super().__init__({"index.query.default_field": list(search_fields)})
