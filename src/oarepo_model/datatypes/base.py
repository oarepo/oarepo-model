from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invenio_base.utils import obj_or_import_string
from marshmallow.fields import Field

if TYPE_CHECKING:
    from .registry import DataTypeRegistry


class DataType:
    """
    Base class for data types in the Oarepo model.
    This class can be extended to create custom data types.
    """

    TYPE = "base"

    marshmallow_field_class: type[Field] | None = None
    jsonschema_type: str | None = None

    def __init__(self, registry: DataTypeRegistry, name: str | None = None):
        """
        Initialize the data type with a registry.
        :param registry: The registry to which this data type belongs.
        """
        self._registry = registry
        self._name = name or self.TYPE

    @property
    def name(self) -> str:
        """
        Get the name of the data type.
        :return: The name of the data type.
        """
        return self._name

    def create_marshmallow_field(
        self, field_name: str, element: dict[str, Any]
    ) -> Field:
        """
        Create a Marshmallow field for the data type.
        This method should be overridden by subclasses to provide specific field creation logic.
        """
        if element.get("marshmallow_field") is not None:
            # if marshmallow_field is specified, use it directly
            return obj_or_import_string(element["marshmallow_field"])

        return self._get_marshmallow_field_class(field_name, element)(
            **self._get_marshmallow_field_args(field_name, element)
        )

    def _get_marshmallow_field_class(
        self, field_name: str, element: dict[str, Any]
    ) -> type[Field]:
        """
        Get the Marshmallow field class for the data type.
        This method can be overridden by subclasses to provide specific field class logic.
        """
        if element.get("marshmallow_field_class") is not None:
            return obj_or_import_string(element["marshmallow_field_class"])

        if self.marshmallow_field_class is None:
            raise NotImplementedError(
                "Subclasses must either provide marshmallow_field_class or "
                "implement this method to provide field class logic."
            )
        return self.marshmallow_field_class

    def _get_marshmallow_field_args(
        self, field_name: str, element: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Get the arguments for the Marshmallow field.
        This method can be overridden by subclasses to provide specific field arguments logic.
        """
        return {
            "required": element.get("required", False),
            "allow_none": element.get("allow_none", False),
        }

    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        """
        Create a JSON schema for the data type.
        This method should be overridden by subclasses to provide specific JSON schema creation logic.
        """
        if self.jsonschema_type is not None:
            return {"type": self.jsonschema_type}

        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement create_json_schema"
        )
