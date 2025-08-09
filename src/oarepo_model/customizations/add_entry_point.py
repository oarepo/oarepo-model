#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Customization for adding entry points to the model.

This module provides the AddEntryPoint customization that registers entry points
in the model's setup configuration. Entry points are specific locations in code
where functionality can be accessed by external systems or plugins, commonly
used for plugin discovery and extension mechanisms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddEntryPoint(Customization):
    """Customization to add an entry point to the model.

    An entry point is a specific location in the code where a certain functionality can be accessed.
    """

    def __init__(
        self,
        group: str,
        name: str,
        value: str,
        separator: str = ":",
        overwrite: bool = False,  # noqa: FBT002 - boolean argument to keep a single class
    ) -> None:
        """Initialize the AddEntryPoint customization.

        :param group: The group to which the entry point belongs.
        :param name: The name of the entry point.
        :param separator: The separator to use in the entry point.
        :param value: The value of the entry point.
        """
        super().__init__(f"{group}::{name}::{value}")
        self.group = group
        self.name = name
        self.separator = separator
        self.value = value
        self.overwrite = overwrite

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        builder.add_entry_point(
            group=self.group,
            name=self.name,
            separator=self.separator,
            value=self.value,
            overwrite=self.overwrite,
        )
