import json
from typing import Any, override

import marshmallow
from invenio_base.utils import obj_or_import_string
from invenio_i18n import gettext as _

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

        if "properties" not in element:
            raise ValueError("Element must contain 'properties' key.")

        properties_fields: dict[str, Any] = {
            key: self._registry.get_type(value).create_marshmallow_field(key, value)
            for key, value in element["properties"].items()
        }

        class Meta:
            unknown = marshmallow.RAISE

        properties_fields["Meta"] = Meta
        return type(self.name, (marshmallow.Schema,), properties_fields)

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
        return {
            **super().create_json_schema(element),
            "properties": {
                key: self._registry.get_type(value).create_json_schema(value)
                for key, value in element["properties"].items()
            },
        }

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        return {
            **super().create_json_schema(element),
            "properties": {
                key: self._registry.get_type(value).create_mapping(value)
                for key, value in element["properties"].items()
            },
        }


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
