#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Boolean data type for OARepo models.

This module provides a boolean data type implementation for use in OARepo models,
supporting checkbox representation in UI forms.
"""

from __future__ import annotations

from typing import Any, override

import marshmallow
from invenio_i18n import gettext

from .base import DataType
from oarepo_runtime.services.facets.utils import _label_for_field


class FormatBoolean(marshmallow.fields.Field):
    """Helper class for formatting single values of booleans."""

    @override
    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the FormatBoolean field."""
        super().__init__(*args, **kwargs)

    @override
    def _serialize(self, value: Any, attr: str | None, obj: Any, **kwargs: Any) -> Any:
        if value is None:
            return None

        yes = gettext("true")
        no = gettext("false")
        return yes if value else no


class BooleanDataType(DataType):
    """Data type for boolean values."""

    TYPE = "boolean"

    marshmallow_field_class = marshmallow.fields.Boolean
    jsonschema_type = "boolean"
    mapping_type = "boolean"

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a Marshmallow UI fields for Boolean value, specifically i18n format."""
        return {
            f"{field_name}_i18n": FormatBoolean(
                attribute=field_name,
            ),
        }

    def get_facet(self, path, element, content=[], facets={}):
        if element.get("searchable", True):
            facet_def = element.get("facet-def")
            if facet_def:
                facets[path] = content + [facet_def]
            else:
                facets[path] = content + [{
                    "facet": "invenio_records_resources.services.records.facets.TermsFacet",
                    "field": path + ".keyword",
                    "label": _label_for_field(path),
                }]
        return facets

    @override
    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
        ret["truthy"] = [True]
        ret["falsy"] = [False]
        return ret
