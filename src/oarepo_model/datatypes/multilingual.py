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
from oarepo_runtime.services.facets.utils import _label_for_field


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
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        lang, value = self.get_multilingual_field(element)
        field_class = self._get_ui_marshmallow_field_class(field_name, element) or I18nStrUIField

        return {field_name: field_class(lang_name=lang, value_name=value)}

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
            value: {"required": True, "type": "fulltext+keyword"},
        }

        ret = super().create_ui_model(element, path)
        ret["children"] = {
            key: self._registry.get_type(value).create_ui_model(value, [*path, key])
            for key, value in element["properties"].items()
        }
        return ret

    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
    ) -> Any:
        """Create facets for the data type."""
        searchable = element.get("searchable", True)

        if searchable:
            lang, _value = self.get_multilingual_field(element)

            facet = [
                *nested_facets,
                {
                    "facet": "oarepo_runtime.services.facets.nested_facet.NestedLabeledFacet",
                    "path": path,
                },
                {
                    "facet": "invenio_records_resources.services.records.facets.TermsFacet",
                    "field": f"{path}.{lang}",
                    "label": _label_for_field(path),
                },
            ]

            facets[path] = facet
        return facets


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
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a UI Marshmallow field for the data type."""
        lang, value = self.get_multilingual_field(element)
        field_class = self._get_ui_marshmallow_field_class(field_name, element) or MultilingualUIField

        return {
            field_name: field_class(lang_name=lang, value_name=value),
        }

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
                "value": {"required": True, "type": "fulltext+keyword"},
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
            "items": {
                "type": "object",
                "properties": {lang: {"type": "string"}, value: {"type": "string"}},
            },
        }

    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
    ) -> Any:
        """Create facets for the data type."""
        searchable = element.get("searchable", True)

        if searchable:
            lang, _value = self.get_multilingual_field(element)

            facet = [
                *nested_facets,
                {
                    "facet": "oarepo_runtime.services.facets.nested_facet.NestedLabeledFacet",
                    "path": path,
                },
                {
                    "facet": "invenio_records_resources.services.records.facets.TermsFacet",
                    "field": f"{path}.{lang}",
                    "label": _label_for_field(path),
                },
            ]

            facets[path] = facet
        return facets


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

    @override
    def create_relations(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> list[Customization]:
        # can not get relations for dynamic objects
        return []
