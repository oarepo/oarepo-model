from typing import Any, override

import marshmallow
from invenio_vocabularies.services.schema import i18n_strings

from oarepo_model.customizations import Customization

from .collections import ObjectDataType


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
    def create_marshmallow_field(
        self, field_name: str, element: dict[str, Any]
    ) -> marshmallow.fields.Field:
        """
        Create a Marshmallow field for the data type.
        This method should be overridden by subclasses to provide specific field creation logic.
        """
        return i18n_strings

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        """
        Create a JSON schema for the data type.
        This method should be overridden by subclasses to provide specific JSON schema creation logic.
        """
        return {"type": "object", "additionalProperties": {"type": "string"}}

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        """
        Create a mapping for the data type.
        This method can be overridden by subclasses to provide specific mapping creation logic.
        """
        return {"type": "object", "dynamic": "true"}

    @override
    def create_relations(
        self, element: dict[str, Any], path: list[tuple[str, dict[str, Any]]]
    ) -> list[Customization]:
        # can not get relations for dynamic objects
        return []
