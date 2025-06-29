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


class AddClass(Customization):
    """Customization to add a class to the model.

    This customization allows you to add a class to the model
    with a specified name and class type.
    """

    def __init__(
        self, name: str, clazz: type | None = None, exists_ok: bool = False
    ) -> None:
        """Initialize the AddClass customization.

        :param name: The name of the class to be added.
        :param clazz: The class type to be added.
        :param exists_ok: Whether to ignore if the class already exists.
        """
        super().__init__(name)
        self.clazz = clazz
        self.exists_ok = exists_ok

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        builder.add_class(self.name, clazz=self.clazz, exists_ok=self.exists_ok)
