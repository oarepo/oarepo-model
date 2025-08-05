#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Numeric data types for OARepo models.

This module provides numeric data type implementations including integers and
floating-point numbers for use in OARepo models.
"""

from __future__ import annotations

from typing import Any, override

import marshmallow.fields
import marshmallow.validate
from babel.numbers import format_decimal
from flask_babel import get_locale

from .base import DataType


class FormatNumber(marshmallow.fields.Field):
    """Helper class for formatting single values of numbers."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the FormatNumber field."""
        super().__init__(*args, **kwargs)

    @override
    def _serialize(self, value: Any, attr: str | None, obj: Any, **kwargs: Any) -> Any:
        if value is None:
            return None

        loc = str(get_locale()) if get_locale() else None

        return format_decimal(value, locale=loc)


class NumberDataType(DataType):
    """Base class for numeric data types."""

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a Marshmallow UI fields for number value."""
        return {
            f"{field_name}": FormatNumber(
                attribute=field_name,
            ),
        }

    @override
    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
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
                        "min_inclusive",
                        element.get("min_exclusive"),
                    ),
                    max=element.get(
                        "max_inclusive",
                        element.get("max_exclusive"),
                    ),
                    min_inclusive=element.get("min_inclusive") is not None,
                    max_inclusive=element.get("max_inclusive") is not None,
                ),
            )
        ret["strict"] = element.get("strict_validation", True)
        return ret

    @override
    def create_ui_model(
        self,
        element: dict[str, Any],
        path: list[str],
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
    """Data type for 32-bit integers."""

    TYPE = "int"

    marshmallow_field_class = marshmallow.fields.Integer
    jsonschema_type = "integer"
    mapping_type = "integer"

    @override
    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
        ret.setdefault("validate", []).append(
            marshmallow.validate.Range(min=-(2**31), max=2**31 - 1),
        )
        ret["strict"] = element.get("strict_validation", True)
        return ret


class LongDataType(NumberDataType):
    """Data type for 64-bit integers (longs)."""

    TYPE = "long"

    marshmallow_field_class = marshmallow.fields.Integer
    jsonschema_type = "integer"
    mapping_type = "long"

    @override
    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
        ret.setdefault("validate", []).append(
            marshmallow.validate.Range(min=-(2**63), max=2**63 - 1),
        )
        ret["strict"] = element.get("strict_validation", True)
        return ret


class FloatDataType(NumberDataType):
    """Data type for single precision floating-point numbers."""

    TYPE = "float"

    marshmallow_field_class = marshmallow.fields.Float
    jsonschema_type = "number"
    mapping_type = "float"

    @override
    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
        ret.setdefault("validate", []).append(
            marshmallow.validate.Range(min=-3.402823466e38, max=3.402823466e38),
        )
        return ret


class DoubleDataType(NumberDataType):
    """Data type for double precision floating-point numbers."""

    TYPE = "double"
    mapping_type = "double"

    marshmallow_field_class = marshmallow.fields.Float
    jsonschema_type = "number"
