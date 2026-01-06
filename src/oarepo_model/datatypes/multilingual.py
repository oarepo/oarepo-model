#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Data type for multilingual dictionary fields.

This module provides the I18nDictDataType class for handling internationalized
text fields that contain translations in multiple languages. The data type
serializes as a dictionary mapping language codes to their respective text
values (e.g., {"en": "English text", "fi": "Finnish text"}).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_vocabularies.services.schema import i18n_strings
from marshmallow import ValidationError

from .collections import ArrayDataType, ObjectDataType

if TYPE_CHECKING:
    import marshmallow


def multilingual_validator(data: list) -> None:
    """Validate language uniqueness."""
    seen = []
    for mult in data:
        lang = mult["lang"]["id"]
        if lang not in seen:
            seen.append(lang)
        else:
            raise ValidationError(f"Duplicated language code {lang}.")


class MultilingualDataType(ArrayDataType):
    """A data type for multilingual dictionaries."""

    TYPE = "multilingual"

    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        field_args = super()._get_marshmallow_field_args(field_name, element)

        field_args.setdefault("validate", []).append(multilingual_validator)
        return field_args


class I18nDictDataType(ObjectDataType):
    """A data type for multilingual dictionaries.

    Their serialization is:
    {
        "en": "English text",
        "fi": "Finnish text",
        ...
    }
    """

    TYPE = "i18ndict"

    @override
    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        """Get properties for the data type."""
        # Note: maybe we should allow defining properties, not a strong need for now
        return {}

    @override
    def create_marshmallow_field(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> marshmallow.fields.Field:
        """Create a Marshmallow field for the data type.

        This method should be overridden by subclasses to provide specific field creation logic.
        """
        return i18n_strings

    @override
    def create_ui_marshmallow_fields(self, field_name: str, element: dict[str, Any]) -> dict[str, Any]:
        return {}  # TODO: create UI field serialization

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create a JSON schema for the data type.

        This method should be overridden by subclasses to provide specific JSON schema creation logic.
        """
        return {"type": "object", "additionalProperties": {"type": "string"}}

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create a mapping for the data type.

        This method can be overridden by subclasses to provide specific mapping creation logic.
        """
        return {"type": "object", "dynamic": "true"}
