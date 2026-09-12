# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Collection data types for OARepo models.

This module provides collection-based data types including arrays, objects,
nested structures, and dynamic objects for use in OARepo models.
"""

from __future__ import annotations

import contextlib
import json
from typing import TYPE_CHECKING, Any, override

import marshmallow
from invenio_base.utils import obj_or_import_string
from invenio_i18n import gettext as _

from oarepo_model.utils import ARRAY_PATH_ITEM, ArrayPathMember, MultiFormatField, convert_to_python_identifier

from .base import ARRAY_ITEM_PATH, DataType, FacetMixin

if TYPE_CHECKING:
    from collections.abc import Mapping

    from oarepo_model.customizations.base import Customization


class NoPropertiesError(Exception):
    """Raised when no properties are found for a data type."""


class NoItemsError(Exception):
    """Raised when no item definition is found for an array data type."""


def _facet_child_path(path: str, key: str) -> str:
    """Build the facet path for a child property named ``key`` under ``path``.

    Compares ``key`` against the *last dot-separated segment* of ``path`` (not
    a substring match) so that a child whose name happens to end with the same
    characters as its parent's path (e.g. parent path "surname", child key
    "name") is not mistaken for the "path already includes this key" case.
    """
    if not path:
        return key
    if path.rsplit(".", 1)[-1] == key:
        return path
    return f"{path}.{key}"


class ObjectDataType(DataType):
    """A data type representing an object in the Oarepo model.

    This class can be extended to create custom object data types.
    """

    TYPE = "object"

    marshmallow_field_class = marshmallow.fields.Nested
    jsonschema_type = "object"
    mapping_type = "object"

    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        """Get the properties for the object data type.

        This method can be overridden by subclasses to provide specific properties logic.
        """
        if "properties" not in element:
            raise NoPropertiesError(f"Element must contain 'properties' key. Got {element}")
        if not isinstance(element["properties"], dict):
            raise TypeError(
                "Element 'properties' must be a dictionary.",
            )
        return element["properties"]

    def create_marshmallow_schema(
        self,
        element: dict[str, Any],
    ) -> type[marshmallow.Schema]:
        """Create a Marshmallow schema for the object data type.

        This method should be overridden by subclasses to provide specific schema creation logic.
        """
        if "marshmallow_schema_class" in element:
            # if marshmallow_schema_class is specified, use it directly
            imported = obj_or_import_string(element["marshmallow_schema_class"])
            if not isinstance(imported, type) or not issubclass(imported, marshmallow.Schema):
                raise ValueError(
                    f"marshmallow_schema_class {element['marshmallow_schema_class']} "
                    "must be a subclass of marshmallow.Schema",
                )
            return imported

        mixins = []
        if "marshmallow_schema_mixins" in element:
            el_mixins = element["marshmallow_schema_mixins"]
            if not isinstance(el_mixins, list):
                raise ValueError("marshmallow_schema_mixins must be a list")
            for mixin in el_mixins:
                imported = obj_or_import_string(mixin)
                if not isinstance(imported, type) or not issubclass(imported, marshmallow.Schema):
                    raise TypeError(
                        f"marshmallow_schema_mixins {mixin} must be a subclass of marshmallow.Schema",
                    )
                mixins.append(imported)

        properties = self._get_properties(element)

        properties_fields: dict[str, Any] = {
            convert_to_python_identifier(key): self._registry.get_type(
                value,
            ).create_marshmallow_field(key, value)
            for key, value in properties.items()
            if not value.get("skip_marshmallow", False)
        }

        class Meta:
            unknown = marshmallow.RAISE

        properties_fields["Meta"] = Meta
        return type(self.name, (*mixins, marshmallow.Schema), properties_fields)

    def create_ui_marshmallow_schema(
        self,
        element: dict[str, Any],
    ) -> type[marshmallow.Schema]:
        """Create a Marshmallow UI schema for the object data type.

        This method should be overridden by subclasses to provide specific schema creation logic.
        """
        if "ui_marshmallow_schema_class" in element:
            # if marshmallow_schema_class is specified, use it directly
            imported = obj_or_import_string(element["ui_marshmallow_schema_class"])
            if not isinstance(imported, type) or not issubclass(imported, marshmallow.Schema):
                raise ValueError(
                    f"ui_marshmallow_schema_class {element['ui_marshmallow_schema_class']} "
                    "must be a subclass of marshmallow.Schema",
                )
            return imported

        properties = self._get_properties(element)

        properties_fields: dict[str, Any] = {}

        for key, value in properties.items():
            properties_fields.update(
                self._registry.get_type(value).create_ui_marshmallow_fields(key, value),
            )

        class Meta:
            unknown = marshmallow.RAISE

        properties_fields["Meta"] = Meta
        return type(self.name, (marshmallow.Schema,), properties_fields)

    @override
    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
        path_suffix: str = "",
        ignored_keys: set[str] | None = None,
    ) -> Any:
        """Create facets for the data type."""
        _ = path_suffix  # path suffix is not used for objects
        with contextlib.suppress(NoPropertiesError):
            properties = self._get_properties(element)
            for key, value in properties.items():
                if ignored_keys is not None and key in ignored_keys:
                    continue
                _path = _facet_child_path(path, key)
                facets.update(self._registry.get_type(value).get_facet(_path, value, nested_facets, facets))

        return facets

    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a Marshmallow UI fields for the object data type.

        This method should be overridden by subclasses to provide specific schema creation logic.
        """
        if element.get("ui_marshmallow_field") is not None:
            # if marshmallow_field is specified, use it directly
            ui_marshmallow_field = obj_or_import_string(element["ui_marshmallow_field"])
            if ui_marshmallow_field is None or not isinstance(ui_marshmallow_field, marshmallow.fields.Field):
                raise TypeError(
                    f"ui_marshmallow_field must be an instance of marshmallow.fields.Field, got {ui_marshmallow_field}",
                )
            return {
                field_name: ui_marshmallow_field,
            }
        field_class = self._get_ui_marshmallow_field_class(field_name, element) or marshmallow.fields.Nested
        return {
            field_name: field_class(
                self.create_ui_marshmallow_schema(element),
            ),
        }

    @override
    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
        # 'nested' is only meaningful for Nested fields; any other field class would
        # swallow it into its metadata and marshmallow would warn about the unknown arg.
        if issubclass(self._get_marshmallow_field_class(field_name, element), marshmallow.fields.Nested):
            ret["nested"] = self.create_marshmallow_schema(element)
        return ret

    @override
    def create_json_schema(self, element: dict[str, Any]) -> Mapping[str, Any]:
        properties = self._get_properties(element)
        return {
            **super().create_json_schema(element),
            "unevaluatedProperties": False,
            "properties": {
                key: self._registry.get_type(value).create_json_schema(value) for key, value in properties.items()
            },
        }

    @override
    def create_mapping(self, element: dict[str, Any]) -> Mapping[str, Any]:
        properties = self._get_properties(element)
        mapping_properties = {}
        for key, value in properties.items():
            datatype = self._registry.get_type(value)
            mapping_properties[key] = datatype.create_mapping(value)
            for dynamic_key, dynamic_mapping in datatype.create_dynamic_mapping(key, value).items():
                mapping_properties.setdefault(dynamic_key, dynamic_mapping)
        return {
            **super().create_mapping(element),
            "dynamic": "strict",
            "properties": mapping_properties,
        }

    @override
    def visit(self, element: dict[str, Any], path: list[str], visitor: Any) -> None:
        """Visit object data type and its properties."""
        super().visit(element, path, visitor)
        for key, value in self._get_properties(element).items():
            self._registry.get_type(value).visit(value, [*path, key], visitor)

    @override
    def create_relations(
        self,
        element: dict[str, Any],
        path: list[ArrayPathMember],
    ) -> list[Customization]:
        """Iterate through the properties of this object and create relations."""
        ret = []
        for key, value in self._get_properties(element).items():
            ret.extend(
                self._registry.get_type(value).create_relations(
                    value,
                    [*path, key],
                ),
            )
        return ret

    @override
    def create_ui_model(
        self,
        element: dict[str, Any],
        path: list[str],
    ) -> dict[str, Any]:
        """Create a UI model for the data type.

        This method should be overridden by subclasses to provide specific UI model creation logic.
        """
        ret = super().create_ui_model(element, path)
        ret["children"] = {
            key: self._registry.get_type(value).create_ui_model(value, [*path, key])
            for key, value in self._get_properties(element).items()
        }
        return ret


class NestedDataType(ObjectDataType):
    """A data type representing a "nested" in the Oarepo model."""

    TYPE = "nested"
    mapping_type = "nested"

    @override
    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
        path_suffix: str = "",
        ignored_keys: set[str] | None = None,
    ) -> Any:
        """Create facets for the data type."""
        _ = path_suffix  # path suffix is not used for nested objects
        with contextlib.suppress(NoPropertiesError):
            properties = self._get_properties(element)
            for key, value in properties.items():
                if ignored_keys is not None and key in ignored_keys:
                    continue
                _path = _facet_child_path(path, key)

                facets.update(
                    self._registry.get_type(value).get_facet(
                        _path,
                        value,
                        nested_facets=[
                            *nested_facets,
                            {
                                "facet": "oarepo_runtime.services.facets.nested_facet.NestedLabeledFacet",
                                "path": path,
                            },
                        ],
                        facets=facets,
                    )
                )
        return facets


def unique_validator(value: list[Any]) -> None:
    """Validate that the array does not contain duplicates."""
    values_as_strings = [json.dumps(item, sort_keys=True) for item in value]
    # get duplicates
    duplicates = {item for item in values_as_strings if values_as_strings.count(item) > 1}
    if duplicates:
        raise marshmallow.ValidationError(
            _("Array contains duplicates: {}").format(", ".join(duplicates)),
        )


class ArrayDataType(FacetMixin, DataType):
    """A data type representing an array in the Oarepo model.

    This class can be extended to create custom array data types.
    """

    TYPE = "array"

    jsonschema_type = "array"
    marshmallow_field_class = marshmallow.fields.List

    def _get_items(self, element: dict[str, Any]) -> dict[str, Any]:
        """Get the items for the array data type.

        This method can be overridden by subclasses to provide specific item logic.
        """
        if "items" not in element:
            raise NoItemsError(f"Element must contain 'items' key. Got {element}")
        if not isinstance(element["items"], dict):
            raise TypeError(
                "Element 'items' must be a dictionary.",
            )
        return element["items"]

    @override
    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        items = self._get_items(element)
        ret = super()._get_marshmallow_field_args(field_name, element)
        ret["cls_or_instance"] = self._registry.get_type(
            items,
        ).create_marshmallow_field(ARRAY_ITEM_PATH, items)
        if "min_items" in element or "max_items" in element:
            ret.setdefault("validate", []).append(
                marshmallow.validate.Length(
                    min=element.get("min_items"),
                    max=element.get("max_items"),
                ),
            )
        if element.get("unique_items"):
            ret.setdefault("validate", []).append(unique_validator)
        return ret

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a Marshmallow UI fields for the array data type.

        This method should be overridden by subclasses to provide specific schema creation logic.
        """
        if element.get("ui_marshmallow_field") is not None:
            # if marshmallow_field is specified, use it directly
            ui_fld = obj_or_import_string(element["ui_marshmallow_field"])
            if ui_fld is None or not isinstance(ui_fld, marshmallow.fields.Field):
                raise TypeError(
                    f"ui_marshmallow_field must be an instance of marshmallow.fields.Field, got {ui_fld}",
                )
            return {
                field_name: ui_fld,
            }

        # retrieve formatting options (e.g. for the date items type -> long, short etc.)
        items_fields = self._registry.get_type(
            self._get_items(element),
        ).create_ui_marshmallow_fields("item", self._get_items(element))
        # no transformations
        if not items_fields:
            return {}

        # if there is only one field, just use it otherwise create a multi-format field
        field = next(iter(items_fields.values())) if len(items_fields) == 1 else MultiFormatField(items_fields)

        # get representation of a marshmallow field
        field_class = self._get_ui_marshmallow_field_class(field_name, element) or marshmallow.fields.List
        return {field_name: field_class(field)}

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        items = self._get_items(element)
        return {
            **super().create_json_schema(element),
            "items": self._registry.get_type(items).create_json_schema(
                items,
            ),
        }

    @override
    def create_mapping(self, element: dict[str, Any]) -> Mapping[str, Any]:
        # skip the array in mapping
        items = self._get_items(element)
        return self._registry.get_type(items).create_mapping(
            items,
        )

    @override
    def visit(self, element: dict[str, Any], path: list[str], visitor: Any) -> None:
        """Visit array data type and its item data type."""
        super().visit(element, path, visitor)
        items = self._get_items(element)
        self._registry.get_type(items).visit(items, [*path, ARRAY_ITEM_PATH], visitor)

    @override
    def create_ui_model(
        self,
        element: dict[str, Any],
        path: list[str],
    ) -> dict[str, Any]:
        """Create a UI model for the data type.

        This method should be overridden by subclasses to provide specific UI model creation logic.
        """
        ret = super().create_ui_model(element, path)
        items = self._get_items(element)
        ret["child"] = self._registry.get_type(items).create_ui_model(
            items,
            [*path, ARRAY_ITEM_PATH],
        )
        if "min_items" in element or "max_items" in element:
            ret["min_items"] = element.get("min_items")
            ret["max_items"] = element.get("max_items")
        if element.get("unique_items"):
            ret["unique_items"] = True
        return ret

    @override
    def create_relations(
        self,
        element: dict[str, Any],
        path: list[ArrayPathMember],
    ) -> list[Customization]:
        items = self._get_items(element)
        return self._registry.get_type(items).create_relations(
            items,
            [*path, ARRAY_PATH_ITEM],
        )

    @override
    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
        path_suffix: str = "",
        ignored_keys: set[str] | None = None,
    ) -> Any:
        """Create facets for the data type."""
        _ = path_suffix, ignored_keys  # not used for arrays
        with contextlib.suppress(NoItemsError):
            value = self._get_items(element)
            if "label" in element and "label" not in value:
                value = {**value, "label": element["label"]}
            facets.update(self._registry.get_type(value).get_facet(path, value, nested_facets, facets))
        return facets


class PermissiveSchema(marshmallow.Schema):
    """A permissive schema that allows any properties."""

    class Meta:
        """Meta class for PermissiveSchema."""

        unknown = marshmallow.INCLUDE


class DynamicObjectDataType(ObjectDataType):
    """A data type for objects whose keys are not known in advance.

    Unlike a regular object, no properties are declared, so any content is accepted:
    {
        "any": "key",
        "can": {"appear": "here"},
        ...
    }

    The value is passed through marshmallow unchanged (fields.Raw), described in
    JSON schema as an object with additionalProperties, and indexed by a dynamic
    OpenSearch mapping. As its keys are unknown, it supports neither relations
    nor UI fields.
    """

    TYPE = "dynamic-object"

    # passes arbitrary JSON through unchanged on both load and dump; a Nested
    # PermissiveSchema would load it fine but dump nothing, as it declares no fields
    marshmallow_field_class = marshmallow.fields.Raw

    @override
    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        """Get properties for the data type."""
        return {}  # dynamic object has no explicit properties

    @override
    def create_marshmallow_schema(
        self,
        element: dict[str, Any],
    ) -> type[marshmallow.Schema]:
        return PermissiveSchema

    @override
    def create_ui_marshmallow_fields(self, field_name: str, element: dict[str, Any]) -> dict[str, Any]:
        return {}

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        return {"type": "object", "additionalProperties": True}

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        return {"type": "object", "dynamic": "true"}

    @override
    def create_relations(
        self,
        element: dict[str, Any],
        path: list[ArrayPathMember],
    ) -> list[Customization]:
        # can not get relations for dynamic objects
        return []
