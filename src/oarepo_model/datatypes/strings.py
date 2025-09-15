#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""String data types for OARepo models.

This module provides string-based data type implementations including basic strings,
keywords, full text fields, and editable text areas for use in OARepo models.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, override

import marshmallow.fields
import marshmallow.validate
from oarepo_runtime.services.facets.utils import get_basic_facet

from .base import DataType


class KeywordDataType(DataType):
    """A data type representing a keyword field in the Oarepo model."""

    TYPE = "keyword"

    marshmallow_field_class = marshmallow.fields.String
    jsonschema_type = "string"
    mapping_type = MappingProxyType(
        {
            "type": "keyword",
            "ignore_above": 256,
        },
    )

    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)

        if "min_length" in element or "max_length" in element:
            ret.setdefault("validate", []).append(
                marshmallow.validate.Length(
                    min=element.get("min_length"),
                    max=element.get("max_length"),
                ),
            )
        if "required" in element and "min_length" not in element:
            # required strings must have min_length set to 1 if it is not already set
            ret.setdefault("validate", []).append(marshmallow.validate.Length(min=1))

        if "enum" in element:
            ret.setdefault("validate", []).append(
                marshmallow.validate.OneOf(element["enum"]),
            )
        if "pattern" in element:
            ret.setdefault("validate", []).append(
                marshmallow.validate.Regexp(element["pattern"]),
            )
        return ret

    @override
    def create_ui_model(
        self,
        element: dict[str, Any],
        path: list[str],
    ) -> dict[str, Any]:
        ret = super().create_ui_model(element, path)
        if "min_length" in element:
            ret["min_length"] = element["min_length"]
        if "max_length" in element:
            ret["max_length"] = element["max_length"]
        if "pattern" in element:
            ret["pattern"] = element["pattern"]
        return ret

    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any] | None = None,
        facets: dict[str, list] | None = None,
    ) -> Any:
        """Create facets for the data type."""
        if facets is None:
            facets = {}
        if nested_facets is None:
            nested_facets = []
        if element.get("searchable", True):
            return get_basic_facet(facets, element.get("facet-def"), path, nested_facets, self.facet_name)
        return facets


class FullTextDataType(KeywordDataType):
    """A data type representing a full-text field in the Oarepo model.

    This class can be extended to create custom full-text data types.
    """

    TYPE = "fulltext"
    mapping_type = MappingProxyType(
        {
            "type": "text",
        },
    )

    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any] | None = None,
        facets: dict[str, list] | None = None,
    ) -> Any:
        """Create facets for the data type."""
        _, _, _, _ = path, element, nested_facets, facets
        return facets


class FulltextWithKeywordDataType(KeywordDataType):
    """A data type representing a full-text field with keyword validation in the Oarepo model.

    This class can be extended to create custom full-text with keyword data types.
    """

    TYPE = "fulltext+keyword"
    mapping_type = MappingProxyType(
        {
            "type": "text",
            "fields": {
                "keyword": {
                    "type": "keyword",
                    "ignore_above": 256,
                },
            },
        }
    )

    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any] | None = None,
        facets: dict[str, list] | None = None,
    ) -> Any:
        """Create facets for the data type."""
        if facets is None:
            facets = {}
        if nested_facets is None:
            nested_facets = []
        if element.get("searchable", True):
            return get_basic_facet(
                facets,
                element.get("facet-def"),
                path,
                nested_facets,
                self.facet_name,
                keyword=True,
            )
        return facets
