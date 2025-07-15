from typing import Any

import marshmallow.fields
import marshmallow.validate

from .base import DataType


class KeywordDataType(DataType):

    TYPE = "keyword"

    marshmallow_field_class = marshmallow.fields.String
    jsonschema_type = "string"
    mapping_type = {
        "type": "keyword",
        "ignore_above": 256,
    }

    def _get_marshmallow_field_args(
        self, field_name: str, element: dict[str, Any]
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)

        if "min_length" in element or "max_length" in element:
            ret.setdefault("validate", []).append(
                marshmallow.validate.Length(
                    min=element.get("min_length", None),
                    max=element.get("max_length", None),
                )
            )
        if "required" in element and "min_length" not in element:
            # required strings must have min_length set to 1 if it is not already set
            ret.setdefault("validate", []).append(marshmallow.validate.Length(min=1))

        if "enum" in element:
            ret.setdefault("validate", []).append(
                marshmallow.validate.OneOf(element["enum"])
            )
        if "pattern" in element:
            ret.setdefault("validate", []).append(
                marshmallow.validate.Regexp(element["pattern"])
            )
        return ret


class FullTextDataType(KeywordDataType):
    """
    A data type representing a full-text field in the Oarepo model.
    This class can be extended to create custom full-text data types.
    """

    TYPE = "fulltext"
    mapping_type = {
        "type": "text",
    }


class FulltextWithKeywordDataType(KeywordDataType):
    """
    A data type representing a full-text field with keyword validation in the Oarepo model.
    This class can be extended to create custom full-text with keyword data types.
    """

    TYPE = "fulltext+keyword"
    mapping_type = {
        "type": "text",
        "fields": {
            "keyword": {
                "type": "keyword",
                "ignore_above": 256,
            },
        },
    }
