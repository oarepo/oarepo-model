from typing import Any, override

import marshmallow.fields
import marshmallow.validate
from babel.numbers import format_decimal
from flask_babel import get_locale

from .base import DataType

class FormatNumber(marshmallow.fields.Field):
    """Helper class for formatting single values of numbers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        
        loc = str(get_locale()) if get_locale() else None
        
        return format_decimal(value, locale=loc)


class NumberDataType(DataType):

    @override
    def create_ui_marshmallow_fields(self, field_name, element):
        """
        Create a Marshmallow UI fields for number value.
        """
        
        return {
            f"{field_name}": FormatNumber(
                attribute=field_name,
            )
        }
    
    @override 
    def _get_marshmallow_field_args(
        self, field_name: str, element: dict[str, Any]
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)

        if (
            "min_inclusive" in element
            or "min_exclusive" in element
            or "max_inclusive" in element
            or "max_exclusive" in element
        ):
            ret.setdefault("validate", []).append(
                marshmallow.validate.Range(
                    min=element.get(
                        "min_inclusive", element.get("min_exclusive", None)
                    ),
                    max=element.get(
                        "max_inclusive", element.get("max_exclusive", None)
                    ),
                    min_inclusive=element.get("min_inclusive", None) is not None,
                    max_inclusive=element.get("max_inclusive", None) is not None,
                )
            )
        ret["strict"] = element.get("strict_validation", True)
        return ret

    def create_ui_model(
        self, element: dict[str, Any], path: list[str]
    ) -> dict[str, Any]:
        ret = super().create_ui_model(element, path)
        if "min_inclusive" in element:
            ret["min_inclusive"] = element["min_inclusive"]
        if "min_exclusive" in element:
            ret["min_exclusive"] = element["min_exclusive"]
        if "max_inclusive" in element:
            ret["max_inclusive"] = element["max_inclusive"]
        if "max_exclusive" in element:
            ret["max_exclusive"] = element["max_exclusive"]
        return ret


class IntegerDataType(NumberDataType):
    TYPE = "int"

    marshmallow_field_class: type[marshmallow.fields.Field] = marshmallow.fields.Integer
    jsonschema_type = "integer"
    mapping_type = "integer"

    @override
    def _get_marshmallow_field_args(
        self, field_name: str, element: dict[str, Any]
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
        ret.setdefault("validate", []).append(
            marshmallow.validate.Range(min=-(2**31), max=2**31 - 1)
        )
        ret["strict"] = element.get("strict_validation", True)
        return ret


class LongDataType(NumberDataType):
    TYPE = "long"

    marshmallow_field_class = marshmallow.fields.Integer
    jsonschema_type = "integer"
    mapping_type = "long"

    @override
    def _get_marshmallow_field_args(
        self, field_name: str, element: dict[str, Any]
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
        ret.setdefault("validate", []).append(
            marshmallow.validate.Range(min=-(2**63), max=2**63 - 1)
        )
        ret["strict"] = element.get("strict_validation", True)
        return ret


class FloatDataType(NumberDataType):
    TYPE = "float"

    marshmallow_field_class = marshmallow.fields.Float
    jsonschema_type = "number"
    mapping_type = "float"

    @override
    def _get_marshmallow_field_args(
        self, field_name: str, element: dict[str, Any]
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
        ret.setdefault("validate", []).append(
            marshmallow.validate.Range(min=-3.402823466e38, max=3.402823466e38)
        )
        return ret


class DoubleDataType(NumberDataType):
    TYPE = "double"
    mapping_type = "double"

    marshmallow_field_class = marshmallow.fields.Float
    jsonschema_type = "number"
