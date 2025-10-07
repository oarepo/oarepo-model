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

from .index_settings import IndexSettings


class AddDefaultSearchFields(IndexSettings):
    """Customization to specify a set of search fields."""

    modifies = ("record-mapping",)

    def __init__(self, *search_fields: str):
        """Initialize the customization with search fields to add."""
        super().__init__({"index.query.default_field": list(search_fields)})
