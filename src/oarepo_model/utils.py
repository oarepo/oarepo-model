#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Utilities for OAREPO model."""

from __future__ import annotations

import json
import keyword
import re
from types import MappingProxyType
from typing import Any, override

import marshmallow

from oarepo_model.c3linearize import LinearizationError, mro_without_class_construction


def is_mro_consistent(class_list: list[type]) -> bool:
    """Check if the MRO of the class list is consistent."""
    try:
        mro = mro_without_class_construction(class_list)
    except LinearizationError:
        return False
    # Check if our classes appear in the same order
    filtered_mro = [c for c in mro if c in class_list]
    return filtered_mro == class_list


def make_mro_consistent(class_list: list[type]) -> list[type]:
    """Make the MRO of the class list consistent.

    This function ensures that the classes in the list can be ordered in a way
    that respects the method resolution order (MRO) of Python classes while
    minimizing the number of changes to the original order.

    :param class_list: List of classes to be ordered.
    :return: A new list of classes ordered to be consistent with MRO.
    :raises TypeError: If the classes cannot be ordered in a way that respects MRO
        or if the classes are incompatible.
    """
    if not class_list:
        return []
    ret = mro_without_class_construction(class_list)
    ret = [x for x in ret if x in class_list]
    return [
        x for x in ret if not any(issubclass(y, x) for y in ret if y != x)
    ]  # keep most specific classes, discard base classes


def camel_case_split(s: str) -> list[str]:
    """Split a camel case string into a list of words."""
    return re.findall(r"([A-Z]?[a-z]+)", s)


def title_case(s: str) -> str:
    """Convert a string to title case."""
    parts = camel_case_split(s)
    return "".join(part.capitalize() for part in parts)


def convert_to_python_identifier(s: str) -> str:
    """Convert a string to a valid Python identifier.

    Replaces invalid characters with their transliteration to english words.

    :param s: The string to convert.
    :return: A valid Python identifier.
    """
    if not s:
        return "_empty_"

    if not s.isidentifier():
        ret = []
        for c in s:
            if not (c.isalnum() or c == "_"):
                ret.append(f"_{ord(c)}_")
            else:
                ret.append(c)
        s = "".join(ret)

    if keyword.iskeyword(s):
        s = f"{s}_"

    return s


class MultiFormatField(marshmallow.fields.Field):
    """A marshmallow field that has multiple internal formatting marshmallow fields.

    During serialization, it uses all the fields and returns a dictionary with
    keys as field names and values as the serialized values.
    """

    def __init__(
        self,
        subfields: dict[str, marshmallow.fields.Field],
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize the field with multiple subfields.

        :param subfields: A dictionary of field names and their corresponding marshmallow fields.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        if len(subfields) < 2:  # noqa: PLR2004   magic constant
            raise ValueError("MultiFormatField requires at least two subfields.")

        self.subfields = subfields

    @override
    def _serialize(
        self,
        value: Any,
        attr: str | None,
        obj: Any,
        **kwargs: Any,
    ) -> Any:
        if value is None:
            return None

        # if there is only 1 format, just return its formatted value
        if len(self.subfields) == 1:
            formatter = next(iter(self.subfields.values()))
            return formatter._serialize(  # noqa: SLF001 private value access
                value,
                attr,
                obj,
                **kwargs,
            )

        # otherwise return key: value dictionary
        return {
            key: field._serialize(  # noqa: SLF001 private value access
                value,
                attr,
                obj,
                **kwargs,
            )
            for key, field in self.subfields.items()
        }


def dump_to_json(obj: Any) -> str:
    """Dump an object to a JSON string."""

    def default_serializer(o: Any) -> Any:
        if isinstance(o, MappingProxyType):
            return dict(o)
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")

    return json.dumps(obj, default=default_serializer)
