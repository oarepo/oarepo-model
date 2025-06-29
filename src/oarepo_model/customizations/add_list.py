#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddList(Customization):
    """Customization to add a list to the model."""

    def __init__(self, name: str, exists_ok: bool = False) -> None:
        """Initialize the AddList customization.

        :param name: The name of the list to be added.
        :param exists_ok: Whether to ignore if the list already exists.
        """
        super().__init__(name)
        self.exists_ok = exists_ok

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        builder.add_list(self.name, exists_ok=self.exists_ok)
