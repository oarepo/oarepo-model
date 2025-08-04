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
from oarepo_runtime.services.schema.i18n import I18nStrField, MultilingualField
from oarepo_runtime.services.schema.i18n_ui import I18nStrUIField, MultilingualUIField

from .base import ARRAY_ITEM_PATH
from .collections import ArrayDataType, ObjectDataType

if TYPE_CHECKING:
    import marshmallow

    from oarepo_model.customizations import Customization


class MultilingualMixin:
    """A mixin containing methods for working with multilingual data types."""

    def get_multilingual_field(self, element: dict) -> tuple[str, str]:
        """Obtain field name modifications."""
        multilingual_def = element.get("multilingual", {})
        lang_name = multilingual_def.get("lang_name", "lang")
        value_name = multilingual_def.get("value_name", "value")
        return lang_name, value_name


class I18nDataType(ObjectDataType, MultilingualMixin):
    """A data type for multilingual dictionaries."""

    TYPE = "i18n"

    @override
    def create_marshmallow_field(self, field_name: str, element: dict[str, Any]) -> marshmallow.fields.Field:
        """Create a Marshmallow field for the data type.

        This method should be overridden by subclasses to provide specific field creation logic.
        """
        lang, value = self.get_multilingual_field(element)
        return I18nStrField(lang_name=lang, value_name=value)

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create a mapping for the data type.

        This method can be overridden by subclasses to provide specific mapping creation logic.
        """
        lang, value = self.get_multilingual_field(element)
        return {
            "type": "nested",
            "properties": {
                lang: {"type": "keyword", "ignore_above": 256},
                value: {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                },
            },
        }

    @override
    def create_ui_marshmallow_schema(self, element: dict[str, Any]) -> type[marshmallow.Schema]:
        lang, value = self.get_multilingual_field(element)

        return I18nStrUIField(lang_name=lang, value_name=value)

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create a JSON schema for the data type.

        This method should be overridden by subclasses to provide specific JSON schema creation logic.
        """
        lang, value = self.get_multilingual_field(element)
        return {
            "type": "object",
            "properties": {lang: {"type": "string"}, value: {"type": "string"}},
        }

    @override
    def create_ui_model(self, element: dict[str, Any], path: list[str]) -> dict[str, Any]:
        """Create a UI model for the data type.

        This method should be overridden by subclasses to provide specific UI model creation logic.
        """
        lang, value = self.get_multilingual_field(element)
        element["properties"] = {
            lang: {"required": True, "type": "keyword"},
            value: {"required": True, "type": "keyword"},
        }

        ret = super().create_ui_model(element, path)
        ret["children"] = {
            key: self._registry.get_type(value).create_ui_model(value, [*path, key])
            for key, value in element["properties"].items()
        }
        return ret


class MultilingualDataType(ArrayDataType, MultilingualMixin):
    """A data type for multilingual dictionaries."""

    TYPE = "multilingual"

    @override
    def create_marshmallow_field(self, field_name: str, element: dict[str, Any]) -> marshmallow.fields.Field:
        """Create a Marshmallow field for the data type.

        This method should be overridden by subclasses to provide specific field creation logic.
        """
        lang, value = self.get_multilingual_field(element)
        return MultilingualField(lang_name=lang, value_name=value)

    @override
    def create_ui_marshmallow_schema(self, element: dict[str, Any]) -> type[marshmallow.Schema]:
        lang, value = self.get_multilingual_field(element)

        return MultilingualUIField(lang_name=lang, value_name=value)

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create a mapping for the data type.

        This method can be overridden by subclasses to provide specific mapping creation logic.
        """
        lang, value = self.get_multilingual_field(element)
        return {
            "type": "nested",
            "properties": {
                lang: {"type": "keyword", "ignore_above": 256},
                value: {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                },
            },
        }

    @override
    def create_ui_model(self, element: dict[str, Any], path: list[str]) -> dict[str, Any]:
        """Create a UI model for the data type.

        This method should be overridden by subclasses to provide specific UI model creation logic.
        """
        element["items"] = {
            "properties": {
                "lang": {"required": True, "type": "keyword"},
                "value": {"required": True, "type": "keyword"},
            },
            "type": "object",
        }
        ret = super().create_ui_model(element, path)
        ret["child"] = self._registry.get_type(element["items"]).create_ui_model(
            element["items"],
            [*path, ARRAY_ITEM_PATH],
        )
        return ret

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create a JSON schema for the data type.

        This method should be overridden by subclasses to provide specific JSON schema creation logic.
        """
        lang, value = self.get_multilingual_field(element)

        return {
            "type": "array",
            "items": {"type": "object", "properties": {lang: {"type": "string"}, value: {"type": "string"}}},
        }


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
    def create_marshmallow_field(self, field_name: str, element: dict[str, Any]) -> marshmallow.fields.Field:
        """Create a Marshmallow field for the data type.

        This method should be overridden by subclasses to provide specific field creation logic.
        """
        return i18n_strings

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

    @override
    def create_relations(self, element: dict[str, Any], path: list[tuple[str, dict[str, Any]]]) -> list[Customization]:
        # can not get relations for dynamic objects
        return []
