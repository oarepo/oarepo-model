# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Boolean data type for OARepo models.

This module provides a boolean data type implementation for use in OARepo models,
supporting checkbox representation in UI forms.
"""

from __future__ import annotations

from typing import Any, override

import marshmallow
from invenio_i18n import gettext

from .base import DataType, FacetMixin


class FormatBoolean(marshmallow.fields.Field):
    """Helper class for formatting single values of booleans."""

    @override
    def _serialize(self, value: Any, attr: str | None, obj: Any, **kwargs: Any) -> Any:
        if value is None:
            return None

        yes = gettext("true")
        no = gettext("false")
        return yes if value else no


class BooleanDataType(FacetMixin, DataType):
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
        field_class = self._get_ui_marshmallow_field_class(field_name, element) or FormatBoolean
        return {
            f"{field_name}_i18n": field_class(attribute=field_name),
        }

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
