#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Customization for creating class lists in the model.

This module provides the AddClassList customization that creates new class lists
with specified names in the model builder. Class lists are collections of classes
that maintain proper method resolution order (MRO) when reordered, making them
suitable for managing inheritance hierarchies and mixin collections.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddClassList(Customization):
    """Customization to add a class list to the model.

    A class list is a collection of classes that will be reordered as least as possible
    to keep the mro.
    """

    def __init__(
        self,
        name: str,
        exists_ok: bool = False,
    ) -> None:
        """Initialize the AddClass customization.

        :param name: The name of the class to be added.
        :param clazz: The class type to be added.
        :param exists_ok: Whether to ignore if the class already exists.
        """
        super().__init__(name)
        self.exists_ok = exists_ok

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        builder.add_class_list(self.name, exists_ok=self.exists_ok)
