from typing import Any

import marshmallow.fields
import marshmallow.validate

from .base import DataType


class NumberDataType(DataType):

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


class IntegerDataType(NumberDataType):
    TYPE = "int"

    marshmallow_field_class: type[marshmallow.fields.Field] = marshmallow.fields.Integer

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

    marshmallow_field_class = marshmallow.fields.Float
