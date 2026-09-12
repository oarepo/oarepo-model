# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

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

    Passing ``value=None`` removes the entry point instead of adding it, which is how a preset
    can take back an entry point registered by another one.

    Entry points are collected straight on the builder and written out at the end of the
    build, so this customization modifies no partial.
    """

    modifies = ()

    def __init__(
        self,
        group: str,
        name: str,
        value: str | None,
        separator: str = ":",
        overwrite: bool = False,
    ) -> None:
        """Initialize the AddEntryPoint customization.

        :param group: The group to which the entry point belongs.
        :param name: The name of the entry point.
        :param separator: The separator to use in the entry point.
        :param value: The value of the entry point, or None to remove it.
        """
        super().__init__(name)
        self.group = group
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
