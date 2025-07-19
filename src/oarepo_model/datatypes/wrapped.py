from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, cast, override

import marshmallow

from .base import DataType

if TYPE_CHECKING:
    from oarepo_model.customizations.base import Customization

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
        return self._registry.get_type(self.type_dict)

    def _merge_type_dict(self, element: dict[str, Any]) -> dict[str, Any]:
        """
        Merge the type_dict with the element dictionary.
        This is used to create a new type dictionary that includes the properties of the element.
        """
        element_without_type = {
            key: value
            for key, value in element.items()
            if key != "type"  # remove type to avoid conflicts
        }
        return strict_merge(self.type_dict, element_without_type)

    @override
    def create_marshmallow_field(
        self, field_name: str, element: dict[str, Any]
    ) -> marshmallow.fields.Field:
        """
        Create a Marshmallow field for the data type.
        This method should be overridden by subclasses to provide specific field creation logic.
        """
        # to create a marshmallow field, we need to merge the element with the type_dict
        return self.impl.create_marshmallow_field(
            field_name, self._merge_type_dict(element)
        )

    @override
    def create_ui_marshmallow_fields(
        self, field_name: str, element: dict[str, Any]
    ) -> marshmallow.fields.Field:
        """
        Create a Marshmallow UI field for the wrapped data type.
        This method should be overridden by subclasses to provide specific field creation logic.
        """
        # to create a marshmallow field, we need to merge the element with the type_dict
        return self.impl.create_ui_marshmallow_fields(
            field_name, self._merge_type_dict(element)
        )
    
    def create_marshmallow_schema(
        self, element: dict[str, Any]
    ) -> type[marshmallow.Schema]:
        """
        Create a Marshmallow schema for the wrapped data type.
        This method should be overridden by subclasses to provide specific schema creation logic.
        """
        return cast(Any, self.impl).create_marshmallow_schema(
            self._merge_type_dict(element)
        )
        
    def create_ui_marshmallow_schema(
        self, element: dict[str, Any]
    ) -> type[marshmallow.Schema]:
        """
        Create a Marshmallow schema for the wrapped data type.
        This method should be overridden by subclasses to provide specific schema creation logic.
        """
        return cast(Any, self.impl).create_ui_marshmallow_schema(
            self._merge_type_dict(element)
        )    

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        return self.impl.create_json_schema(self._merge_type_dict(element))

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        return self.impl.create_mapping(self._merge_type_dict(element))

    @override
    def create_relations(
        self, element: dict[str, Any], path: list[tuple[str, dict[str, Any]]]
    ) -> list[Customization]:
        return self.impl.create_relations(self._merge_type_dict(element), path)


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
