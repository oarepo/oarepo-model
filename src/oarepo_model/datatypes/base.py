from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invenio_base.utils import obj_or_import_string
from marshmallow.fields import Field

if TYPE_CHECKING:
    from oarepo_model.customizations.base import Customization

    from .registry import DataTypeRegistry

ARRAY_ITEM_PATH = "[]"


class DataType:
    """
    Base class for data types in the Oarepo model.
    This class can be extended to create custom data types.
    """

    TYPE = "base"

    marshmallow_field_class: type[Field] | None = None
    jsonschema_type: str | None = None
    mapping_type: str | dict[str, Any] | None = None

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

    def create_ui_marshmallow_fields(
        self, field_name: str, element: dict[str, Any]
    ) -> dict[str, Field]:
        """
        Create a Marshmallow UI field for the data type.
        This method should be overridden by subclasses to provide specific UI field creation logic.
        """
        # if there is no UI transformation, leave it out, therefore there are no copied values in UI
        return {}

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
            "dump_only": element.get("dump_only", False),
            "load_only": element.get("load_only", False),
            "attribute": field_name,
            "data_key": field_name,
        }

    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        """
        Create a JSON schema for the data type.
        This method should be overridden by subclasses to provide specific JSON schema creation logic.
        """
        if self.jsonschema_type is not None:
            return {"type": self.jsonschema_type}

        raise NotImplementedError(
            f"{self.__class__.__name__} neither implements create_json_schema nor provides self.jsonschema_type"
        )

    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        """
        Create a mapping for the data type.
        This method can be overridden by subclasses to provide specific mapping creation logic.
        """
        if self.mapping_type is not None:
            if isinstance(self.mapping_type, dict):
                return self.mapping_type
            return {"type": self.mapping_type}

        raise NotImplementedError(
            f"{self.__class__.__name__} neither implements create_mapping nor provides self.mapping_type"
        )

    def create_relations(
        self, element: dict[str, Any], path: list[tuple[str, dict[str, Any]]]
    ) -> list[Customization]:
        """
        Create relations for the data type.
        This method can be overridden by subclasses to provide specific relations creation logic.
        """
        return []

    def create_ui_model(
        self, element: dict[str, Any], path: list[str]
    ) -> dict[str, Any]:
        """
        Create a UI model for the data type.
        This method should be overridden by subclasses to provide specific UI model creation logic.
        """

        # replace array items:
        # a,[],b => a,b
        # a, [], b, [] => a, b, item
        replaced_arrays = [x for x in path[:-1] if x is not ARRAY_ITEM_PATH]
        if path[-1] is ARRAY_ITEM_PATH:
            # if the last element is ARRAY_ITEM_PATH, we replace it with "item"
            replaced_arrays.append("item")
        else:
            replaced_arrays.append(path[-1])

        target_path = "/".join(replaced_arrays)

        ret: dict[str, Any] = {
            "help": (
                element["help.key"] if "help.key" in element else f"{target_path}.help"
            ),
            "label": (
                element["label.key"]
                if "label.key" in element
                else f"{target_path}.label"
            ),
            "hint": (
                element["hint.key"] if "hint.key" in element else f"{target_path}.hint"
            ),
        }
        if "required" in element and element["required"]:
            ret["required"] = True

        if "input" in element:
            ret["input"] = element["input"]
        else:
            ret["input"] = element["type"]

        return ret
