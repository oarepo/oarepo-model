from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, override

from .base import DataType

if TYPE_CHECKING:
    from .registry import DataTypeRegistry


class WrappedDataType(DataType):
    """A datatype that wraps a dictionary defining the type."""

    def __init__(
        self, registry: DataTypeRegistry, name: str, type_dict: dict[str, Any]
    ):
        super().__init__(registry, name)
        self.type_dict = type_dict
        self._impl: DataType | None = None

    @cached_property
    def impl(self) -> DataType:
        type_name = self.type_dict.get("type")
        if not type_name:
            raise ValueError("Type dictionary must contain a 'type' key.")
        return self._registry.get_type(type_name)

    @override
    def create_marshmallow_field(self, field_name: str, element: dict[str, Any]) -> Any:
        """
        Create a Marshmallow field for the data type.
        This method should be overridden by subclasses to provide specific field creation logic.
        """
        # to create a marshmallow field, we need to merge the element with the type_dict
        element_without_type = {
            key: value
            for key, value in element.items()
            if key != "type"  # remove type to avoid conflicts
        }
        merged = strict_merge(self.type_dict, element_without_type)
        return self.impl.create_marshmallow_field(field_name, merged)


def strict_merge(a, b):
    """
    Merge two dictionaries, arrays or other types. In dictionaries, one element
    can not override another element with the same key.
    """
    match a:
        case dict():
            if not isinstance(b, dict):
                raise TypeError(f"Cannot merge dict with {type(b)}")
            if not a.keys().isdisjoint(b.keys()):
                raise ValueError(
                    f"Cannot merge dictionaries with overlapping keys: {a.keys() & b.keys()}"
                )
            return {**a, **b}
        case list():
            if not isinstance(b, list):
                raise TypeError(f"Cannot merge list with {type(b)}")
            return a + b
        case _:
            if a != b:
                raise TypeError(f"Cannot merge {type(a)} with {type(b)}")
            return a
