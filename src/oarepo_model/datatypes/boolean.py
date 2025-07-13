from typing import Any

import marshmallow

from .base import DataType


class BooleanDataType(DataType):
    TYPE = "boolean"

    marshmallow_field_class = marshmallow.fields.Boolean

    def _get_marshmallow_field_args(
        self, field_name: str, element: dict[str, Any]
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
        ret["truthy"] = [True]
        ret["falsy"] = [False]
        return ret
