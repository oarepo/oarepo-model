#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddToList(Customization):
    """Customization to add a value to a list in the model."""

    def __init__(self, list_name: str, value: Any, exists_ok: bool = False) -> None:
        """Initialize the AddToList customization."""
        super().__init__(list_name)
        self.value = value
        self.exists_ok = exists_ok

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        d = builder.add_list(self.name, exists_ok=True)
        if self.value in d and not self.exists_ok:
            raise ValueError(
                f"Value '{self.value}' already exists in list '{self.name}'."
            )
        d.append(self.value)
