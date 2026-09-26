# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Customization for adding values to lists in the model.

This module provides the AddToList customization that allows appending new
values to existing lists in the model builder. It supports checking for
existing values to prevent duplicates when the exists_ok parameter is False.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddToList(Customization):
    """Customization to add a value to a list in the model."""

    def __init__(
        self,
        list_name: str,
        value: Any,
        exists_ok: bool = False,
    ) -> None:
        """Initialize the AddToList customization."""
        super().__init__(list_name)
        self.value = value
        self.exists_ok = exists_ok

    modifies_own_name = True

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        d = builder.get_list(self.name)
        if self.value in d and not self.exists_ok:
            raise ValueError(
                f"Value '{self.value}' already exists in list '{self.name}'.",
            )
        d.append(self.value)
