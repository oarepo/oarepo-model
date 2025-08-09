#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Customization for adding properties to modules.

This module provides the AddToModule customization that allows adding new
properties with specified values to existing modules in the model. This is
useful for extending modules with configuration variables, constants, or
other module-level attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddToModule(Customization):
    """Customization to add a property to a module to the model."""

    def __init__(
        self,
        module_name: str,
        property_name: str,
        value: Any,
        exists_ok: bool = False,  # noqa: FBT002 - boolean argument to keep a single class
    ) -> None:
        """Initialize the AddToModule customization.

        :param module_name: The name of the module to be added.
        :param property_name: The name of the property to be added to the module.
        :param value: The value of the property to be added to the module.
        :param exists_ok: Whether to ignore if the module already exists.
        """
        super().__init__(module_name)
        self.property_name = property_name
        self.value = value
        self.exists_ok = exists_ok

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        ret = builder.get_module(self.name)
        if hasattr(ret, self.property_name) and not self.exists_ok:
            raise ValueError(
                f"Property '{self.property_name}' already exists in module '{self.name}'.",
            )
        setattr(ret, self.property_name, self.value)
