# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""String data types: ``keyword``, ``fulltext``, ``fulltext+keyword`` and ``url``.

Pick the type by how the value will be searched:

- ``keyword`` - exact match, sorting and facets (identifiers, statuses, categories).
  Indexed with ``ignore_above: 256``: longer values are stored, but not indexed.
- ``fulltext`` - analyzed text searched by words (abstracts, descriptions). No facet
  and no sorting.
- ``fulltext+keyword`` - both: analyzed text plus an exact ``.keyword`` sub-field that
  is used for the facet and for sorting (titles, names).
- ``url`` - an absolute http, https, ftp or ftps URL, indexed as a keyword with
  ``ignore_above: 2048``.

All of them accept ``min_length``, ``max_length``, ``enum`` and ``pattern``. A
``required`` field without ``min_length`` also rejects an empty string.

Example (model YAML):

```yaml
title:
  type: fulltext+keyword
  required: true
publication_status:
  type: keyword
  enum: [draft, published, retracted]
abstract:
  type: fulltext
  max_length: 5000
landing_page:
  type: url
```

See https://nrp-cz.github.io/docs/customize/model_backend/model_reference#text-data-types
"""

from __future__ import annotations

from typing import Any, override

import marshmallow.fields
import marshmallow.validate

from oarepo_model.utils import ReadOnlyDict

from .base import DataType, FacetMixin


class KeywordDataType(FacetMixin, DataType):
    """A data type representing a keyword field in the Oarepo model."""

    TYPE = "keyword"

    marshmallow_field_class = marshmallow.fields.String
    jsonschema_type = "string"
    mapping_type = ReadOnlyDict(
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
        if element.get("required") and "min_length" not in element:
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


class UrlDataType(KeywordDataType):
    """An absolute URL (http, https, ftp, ftps), indexed as a keyword."""

    TYPE = "url"

    marshmallow_field_class = marshmallow.fields.Url
    jsonschema_type = ReadOnlyDict({"type": "string", "format": "uri"})
    # URLs are often longer than the 256 chars of a plain keyword
    mapping_type = ReadOnlyDict(
        {
            "type": "keyword",
            "ignore_above": 2048,
        },
    )


class FullTextDataType(KeywordDataType):
    """A data type representing a full-text field in the Oarepo model.

    This class can be extended to create custom full-text data types.
    """

    TYPE = "fulltext"
    mapping_type = ReadOnlyDict(
        {
            "type": "text",
        },
    )

    @override
    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
        path_suffix: str = "",
        ignored_keys: set[str] | None = None,
    ) -> Any:
        """Do not create facets for the fulltext data type."""
        _, _, _, _, _, _ = (
            path,
            element,
            nested_facets,
            facets,
            path_suffix,
            ignored_keys,
        )  # to avoid unused variable warning
        return facets


class FulltextWithKeywordDataType(KeywordDataType):
    """A data type representing a full-text field with keyword validation in the Oarepo model.

    This class can be extended to create custom full-text with keyword data types.
    """

    TYPE = "fulltext+keyword"
    mapping_type = ReadOnlyDict(
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

    @override
    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
        path_suffix: str = "",
        ignored_keys: set[str] | None = None,
    ) -> Any:
        """Create facets for the .keyword part of the fulltext+keyword type."""
        _ = ignored_keys
        return super().get_facet(
            path,
            element,
            nested_facets,
            facets,
            path_suffix=path_suffix or ".keyword",
        )
