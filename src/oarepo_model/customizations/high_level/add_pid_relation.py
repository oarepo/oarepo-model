#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""High-level customization for adding PID relations to models.

This module provides the AddPIDRelation customization that creates appropriate
PID relation system fields based on the path structure. It supports simple
relations, list relations, and nested list relations by analyzing the presence
and position of array items in the relation path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.records.systemfields import (
    PIDListRelation,
    PIDNestedListRelation,
    PIDRelation,
)

from ..base import Customization

if TYPE_CHECKING:
    from invenio_records_resources.records.systemfields.pid import PIDField

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class ARRAY_PATH_ITEM:  # noqa: N801
    """Marker for array items in the path.

    This class is used to indicate that a part of the path is an array item.
    It is used to differentiate between simple relations and list relations.
    """


class AddPIDRelation(Customization):
    """Customization to add PID relations to the model."""

    def __init__(
        self,
        name: str,
        path: list[str | type[ARRAY_PATH_ITEM]],
        keys: list[str],
        pid_field: PIDField,
        cache_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the AddPIDRelation customization.

        :param path: The path to the relation.
        :param keys: The keys for the relation.
        """
        super().__init__("add_pid_relation")
        self.name = name
        self.path = path
        self.keys = keys
        self.pid_field = pid_field
        self.cache_key = cache_key
        self.kwargs = kwargs

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        relations = builder.get_dictionary("relations")
        array_count = self.path.count(ARRAY_PATH_ITEM)
        match array_count:
            case 0:
                relations[self.name] = PIDRelation(
                    ".".join(x for x in self.path if isinstance(x, str)),
                    keys=self.keys,
                    pid_field=self.pid_field,
                    cache_key=self.cache_key,
                    **self.kwargs,
                )
            case 1:
                before_array = self.path[: self.path.index(ARRAY_PATH_ITEM)]
                after_array = self.path[self.path.index(ARRAY_PATH_ITEM) + 1 :]

                # If the last element is an array, we create a PIDListRelation
                relations[self.name] = PIDListRelation(
                    ".".join(x for x in before_array if isinstance(x, str)),
                    keys=self.keys,
                    pid_field=self.pid_field,
                    cache_key=self.cache_key,
                    relation_field=(".".join(x for x in after_array if isinstance(x, str)) if after_array else None),
                    **self.kwargs,
                )

            case 2:
                first_array_index = self.path.index(ARRAY_PATH_ITEM)
                second_array_index = self.path.index(
                    ARRAY_PATH_ITEM,
                    first_array_index + 1,
                )
                before_first_array = self.path[:first_array_index]
                between_arrays = self.path[first_array_index + 1 : second_array_index]
                after_second_array = self.path[second_array_index + 1 :]

                if after_second_array:
                    raise NotImplementedError(
                        "Relations within nested arrays of objects are not supported yet.",
                    )

                relations[self.name] = PIDNestedListRelation(
                    ".".join(x for x in before_first_array if isinstance(x, str)),
                    relation_field=(
                        ".".join(x for x in between_arrays if isinstance(x, str)) if between_arrays else None
                    ),
                    keys=self.keys,
                    pid_field=self.pid_field,
                    cache_key=self.cache_key,
                    **self.kwargs,
                )

            case _:
                raise NotImplementedError(
                    "Only one or two arrays in the path are supported for PID relations.",
                )
