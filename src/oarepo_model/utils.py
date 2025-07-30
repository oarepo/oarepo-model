#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
import inspect
import keyword
import re

import marshmallow
from invenio_db import db


def add_to_class_list_preserve_mro(
    class_list: list[type], clz: type, prepend: bool = False
) -> None:
    if not inspect.isclass(clz):
        raise TypeError("Only classes can be added to ClassList")

    # Remove existing base class if it is a subclass of the new class
    for item in class_list:
        if issubclass(item, clz):
            # already an inherited class from this class is present, do nothing
            return

    # Choose enumeration direction based on insert_func
    idx = 0
    removed_positions = []
    while idx < len(class_list):
        item = class_list[idx]
        if issubclass(clz, item):
            removed_positions.append(idx)
            del class_list[idx]
        else:
            idx += 1

    if removed_positions:
        if prepend:
            # If we are prepending, we need to insert at the start
            class_list.insert(removed_positions[0], clz)
        else:
            class_list.insert(removed_positions[-1], clz)
    else:
        # If no class was removed, we append the new class
        if prepend:
            class_list.insert(0, clz)
        else:
            class_list.append(clz)

    # Ensure the order is consistent with MRO
    if is_mro_consistent(class_list):
        return

    values = list(class_list)
    class_list.clear()
    class_list.extend(make_mro_consistent(values))


def is_mro_consistent(class_list: list[type]) -> bool:
    try:
        # Directly attempt to create the MRO
        created_class = type("_", tuple(class_list), {})
        mro = created_class.mro()
        # If the created class is sqlalchemy, remove it from sqlachemy mapping
        if issubclass(created_class, db.Model):
            db.Model.registry._dispose_cls(created_class)
        # Check if our classes appear in the same order
        filtered_mro = [c for c in mro if c in class_list]
        return filtered_mro == class_list
    except TypeError:
        return False


def make_mro_consistent(class_list: list[type]) -> list[type]:
    if not class_list:
        return []

    # Start with the first class
    result = []
    result.append(class_list[0])

    try:
        for cls in class_list[1:]:
            # Find the best position to insert the current class
            insert_pos = len(result)

            # Check all possible positions from right to left
            for i in range(len(result), -1, -1):
                try:
                    # Test if inserting at position i would be valid
                    temp_order = result[:i] + [cls] + result[i:]
                    created_class = type("_", tuple(temp_order), {})
                    if issubclass(created_class, db.Model):
                        db.Model.registry._dispose_cls(created_class)
                    insert_pos = i
                    break
                except TypeError:
                    continue
            else:
                raise TypeError(
                    f"Cannot insert {cls} into MRO of {result}. "
                    "It would break the method resolution order."
                )

            # Insert at the found position
            result.insert(insert_pos, cls)
    except Exception as e:
        raise TypeError(
            f"Failed to make MRO consistent for {class_list}. "
            "Ensure that the classes are compatible."
        ) from e
    return result


def camel_case_split(s):
    return re.findall(r"([A-Z]?[a-z]+)", s)


def title_case(s):
    parts = camel_case_split(s)
    return "".join(part.capitalize() for part in parts)


def convert_to_python_identifier(s: str) -> str:
    """
    Convert a string to a valid Python identifier.
    Replaces invalid characters with their transliteration to english words.
    """
    if not s:
        return "_empty_"

    if not s.isidentifier():
        ret = []
        for c in s:
            if not (c.isalnum() or c == '_'):
                ret.append(f"_{ord(c)}_")
            else:
                ret.append(c)
        s = "".join(ret)

    if keyword.iskeyword(s):
        s = f"{s}_"

    return s


class PossibleMultiFormatField(marshmallow.fields.Field):
    """Helper class to wrap around different formatting options of a marshmallow field.

    Class keeps different formatters (e.g. for boolean or number).
    Returns only formatted value if there is only 1 formatter or wrapped in a dictionary (see date example in test_ui_schemas).
    """

    def __init__(
        self, formatters: dict[str, marshmallow.fields.Field], *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.formatters = formatters

    def _serialize(self, value, attr, obj, **kwargs) -> dict[str, str] | str:
        if value is None:
            return None

        # if there is only 1 format, just return its formatted value
        if len(self.formatters) == 1:
            formatter = next(iter(self.formatters))
            return formatter._serialize(value, attr, obj, **kwargs)

        # otherwise return key: value dictionary
        return {
            key: field._serialize(value, attr, obj, **kwargs)
            for key, field in self.formatters.items()
        }

    def as_marshmallow_field(
        self,
    ) -> dict[str, marshmallow.fields.Field] | marshmallow.fields.Field:
        if (
            len(self.formatters) >= 2
        ):  # return self if there are multiple formatting (serialization is handled by this class too)
            return self
        return next(
            iter(self.formatters.values())
        )  # return only formatted value, so there is no key in the output
