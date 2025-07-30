import importlib.metadata
import logging
from typing import Any

from .base import DataType
from .wrapped import WrappedDataType

log = logging.getLogger("oarepo_model")


class DataTypeRegistry:
    """
    Registry for types used in the model.
    This is a placeholder for the actual implementation.
    """

    def __init__(self) -> None:
        self.types: dict[str, DataType] = {}

    def load_entry_points(self) -> None:
        """
        Load types from entry points.
        This is a placeholder for the actual implementation.
        """
        for ep in importlib.metadata.entry_points(group="oarepo_model.datatypes"):
            self.add_types(ep.load())

    def add_types(self, type_dict: dict[str, Any]):
        """
        Add types to the registry from a dictionary.
        :param type_dict: A dictionary where keys are type names and values are either DataType
                         subclasses or dictionaries defining the type.
        """
        self._unwind_shortcuts_in_properties(type_dict)

        for type_name, type_cls_or_dict in type_dict.items():
            if isinstance(type_cls_or_dict, dict):
                self.register(
                    type_name, WrappedDataType(self, type_name, type_cls_or_dict)
                )
            elif issubclass(type_cls_or_dict, DataType):
                self.register(type_name, type_cls_or_dict(self, type_name))
            else:
                raise TypeError(
                    f"Invalid type for {type_name}: {type_cls_or_dict}. "
                    "Expected a dict or a subclass of DataType."
                )

    def register(self, type_name: str, datatype: DataType):
        """
        Register a data type in the registry.
        """
        if type_name in self.types:
            log.warning(f"Type {type_name} is already registered, overwriting.")
        self.types[type_name] = datatype

    def get_type(self, type_name_or_dict: str | dict[str, Any]) -> DataType:
        """
        Get a data type by its name.

        :param type_name: The name of the data type.
        :return: The data type instance.
        """
        if isinstance(type_name_or_dict, dict):
            if "type" in type_name_or_dict:
                type_name = type_name_or_dict["type"]
            elif "properties" in type_name_or_dict:
                type_name = "object"
            elif "items" in type_name_or_dict:
                type_name = "array"
            else:
                raise ValueError(f"Can not get type from {type_name_or_dict}")
        else:
            type_name = type_name_or_dict

        if type_name not in self.types:
            raise KeyError(f"Data type '{type_name}' is not registered.")
        return self.types[type_name]

    def _unwind_shortcuts_in_properties(
        self, type_dict: dict[str, Any]
    ) -> dict[str, Any]:
        ret: dict[str, Any] = {}
        for k, v in type_dict.items():
            if k.endswith("[]"):
                v = {"type": "array", "items": v}
            v = self._unwind_shortcuts(v)
            ret[k] = v
        return ret

    def _unwind_shortcuts(self, v):
        if not isinstance(v, dict):
            return v
        if "properties" in v:
            v["properties"] = self._unwind_shortcuts_in_properties(v["properties"])
        elif "items" in v:
            v["items"] = self._unwind_shortcuts(v["items"])
        return v
