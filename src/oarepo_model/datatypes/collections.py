from __future__ import annotations

import json
from typing import Any, override

import marshmallow
from invenio_base.utils import obj_or_import_string
from invenio_i18n import gettext as _

from oarepo_model.customizations.base import Customization
from oarepo_model.utils import PossibleMultiFormatField, convert_to_python_identifier

from .base import DataType


class ObjectDataType(DataType):
    """
    A data type representing an object in the Oarepo model.
    This class can be extended to create custom object data types.
    """

    TYPE = "object"

    marshmallow_field_class = marshmallow.fields.Nested
    jsonschema_type = "object"
    mapping_type = "object"

    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        """
        Get the properties for the object data type.
        This method can be overridden by subclasses to provide specific properties logic.
        """
        if "properties" not in element:
            raise ValueError("Element must contain 'properties' key.")
        return element["properties"]

    def create_marshmallow_schema(
        self, element: dict[str, Any]
    ) -> type[marshmallow.Schema]:
        """
        Create a Marshmallow schema for the object data type.
        This method should be overridden by subclasses to provide specific schema creation logic.
        """
        if "marshmallow_schema_class" in element:
            # if marshmallow_schema_class is specified, use it directly
            return obj_or_import_string(element["marshmallow_schema_class"])

        properties = self._get_properties(element)

        # TODO: create marshmallow field should pass extra arguments such attribute and data_key
        properties_fields: dict[str, Any] = {
            convert_to_python_identifier(key): self._registry.get_type(
                value
            ).create_marshmallow_field(key, value)
            for key, value in properties.items()
            if not value.get("skip_marshmallow", False)
        }

        class Meta:
            unknown = marshmallow.RAISE

        properties_fields["Meta"] = Meta
        return type(self.name, (marshmallow.Schema,), properties_fields)

    def create_ui_marshmallow_schema(
        self, element: dict[str, Any]
    ) -> type[marshmallow.Schema]:
        """
        Create a Marshmallow UI schema for the object data type.
        This method should be overridden by subclasses to provide specific schema creation logic.
        """

        if "ui_marshmallow_schema_class" in element:
            # if marshmallow_schema_class is specified, use it directly
            return obj_or_import_string(element["ui_marshmallow_schema_class"])

        if "properties" not in element:
            raise ValueError("Element must contain 'properties' key.")

        properties_fields: dict[str, Any] = {}

        for key, value in element["properties"].items():
            properties_fields.update(
                self._registry.get_type(value).create_ui_marshmallow_fields(key, value)
            )

        class Meta:
            unknown = marshmallow.RAISE

        properties_fields["Meta"] = Meta
        return type(self.name, (marshmallow.Schema,), properties_fields)

    def create_ui_marshmallow_fields(
        self, field_name: str, element: dict[str, Any]
    ) -> dict[str, ObjectDataType]:
        """
        Create a Marshmallow UI fields for the object data type.
        This method should be overridden by subclasses to provide specific schema creation logic.
        """
        if element.get("ui_marshmallow_field") is not None:
            # if marshmallow_field is specified, use it directly
            return {
                field_name: obj_or_import_string(element.get("ui_marshmallow_field"))
            }

        return {
            field_name: marshmallow.fields.Nested(
                self.create_ui_marshmallow_schema(element)
            )
        }

    @override
    def _get_marshmallow_field_args(
        self, field_name: str, element: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "nested": self.create_marshmallow_schema(element),
            **super()._get_marshmallow_field_args(field_name, element),
        }

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        properties = self._get_properties(element)
        return {
            **super().create_json_schema(element),
            "unevaluatedProperties": False,
            "properties": {
                key: self._registry.get_type(value).create_json_schema(value)
                for key, value in properties.items()
            },
        }

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        properties = self._get_properties(element)
        return {
            **super().create_mapping(element),
            "dynamic": "strict",
            "properties": {
                key: self._registry.get_type(value).create_mapping(value)
                for key, value in properties.items()
            },
        }

    @override
    def create_relations(
        self, element: dict[str, Any], path: list[tuple[str, dict[str, Any]]]
    ) -> list[Customization]:
        """
        Iterate through the properties of this object and create relations.
        """
        ret = []
        for key, value in self._get_properties(element).items():
            ret.extend(
                self._registry.get_type(value).create_relations(
                    value, path + [(key, value)]
                )
            )
        return ret


class NestedDataType(ObjectDataType):
    """
    A data type representing a "nested" in the Oarepo model.
    """

    TYPE = "nested"
    mapping_type = "nested"


def unique_validator(value: list[Any]) -> None:
    values_as_strings = [json.dumps(item, sort_keys=True) for item in value]
    # get duplicates
    duplicates = set(
        item for item in values_as_strings if values_as_strings.count(item) > 1
    )
    if duplicates:
        raise marshmallow.ValidationError(
            _("Array contains duplicates: {}").format(", ".join(duplicates))
        )


class ArrayDataType(DataType):
    """
    A data type representing an array in the Oarepo model.
    This class can be extended to create custom array data types.
    """

    TYPE = "array"

    jsonschema_type = "array"
    marshmallow_field_class = marshmallow.fields.List

    @override
    def _get_marshmallow_field_args(
        self, field_name: str, element: dict[str, Any]
    ) -> dict[str, Any]:
        if "items" not in element:
            raise ValueError("Element must contain 'items' key.")
        ret = super()._get_marshmallow_field_args(field_name, element)
        ret["cls_or_instance"] = self._registry.get_type(
            element["items"]
        ).create_marshmallow_field("[]", element["items"])
        if "min_items" in element or "max_items" in element:
            ret.setdefault("validate", []).append(
                marshmallow.validate.Length(
                    min=element.get("min_items", None),
                    max=element.get("max_items", None),
                )
            )
        if "unique_items" in element and element["unique_items"]:
            ret.setdefault("validate", []).append(unique_validator)
        return ret

    @override
    def create_ui_marshmallow_fields(self, field_name, element):
        """
        Create a Marshmallow UI fields for the array data type.
        This method should be overridden by subclasses to provide specific schema creation logic.
        """
        if element.get("ui_marshmallow_field") is not None:
            # if marshmallow_field is specified, use it directly
            return {
                field_name: obj_or_import_string(element.get("ui_marshmallow_field"))
            }

        # retrieve formatting options (e.g. for the date items type -> long, short etc.)
        items_fields = self._registry.get_type(
            element["items"]
        ).create_ui_marshmallow_fields("item", element["items"])
        # no transformations
        if not items_fields:
            return {}

        # create helper class that wraps all formatting options
        fields = PossibleMultiFormatField(items_fields)
        # get representation of a marshmallow field
        return {field_name: marshmallow.fields.List(fields.as_marshmallow_field())}

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        return {
            **super().create_json_schema(element),
            "items": self._registry.get_type(element["items"]).create_json_schema(
                element["items"]
            ),
        }

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        # skip the array in mapping
        return self._registry.get_type(element["items"]).create_mapping(
            element["items"]
        )

    @override
    def create_relations(
        self, element: dict[str, Any], path: list[tuple[str, dict[str, Any]]]
    ) -> list[Customization]:
        return self._registry.get_type(element["items"]).create_relations(
            element["items"], path + [("", element)]
        )


class PermissiveSchema(marshmallow.Schema):
    """A permissive schema that allows any properties."""

    class Meta:
        unknown = marshmallow.INCLUDE


class DynamicObjectDataType(ObjectDataType):
    """A data type for multilingual dictionaries.

    Their serialization is:
    {
        "en": "English text",
        "fi": "Finnish text",
        ...
    }
    """

    TYPE = "dynamic-object"

    def create_marshmallow_schema(
        self, element: dict[str, Any]
    ) -> type[marshmallow.Schema]:
        return PermissiveSchema

    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        return {"type": "object", "additionalProperties": True}

    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        return {"type": "object", "dynamic": "true"}

    @override
    def create_relations(
        self, element: dict[str, Any], path: list[tuple[str, dict[str, Any]]]
    ) -> list[Customization]:
        # can not get relations for dynamic objects
        return []
