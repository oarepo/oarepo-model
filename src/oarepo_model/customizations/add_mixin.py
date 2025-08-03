#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Customization for adding mixins to OARepo model classes.

This module provides the AddMixins customization that allows adding mixin classes
to existing classes in an OARepo model during the building process.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddMixins(Customization):
    """Customization to add a mixin to the model.

    This customization allows you to add a mixin to the model
    with a specified name and class type.
    """

    def __init__(self, name: str, *clazz: type) -> None:
        """Initialize the AddMixins customization.

        :param name: The name of the mixin to be added.
        :param clazz: The class type to be added.
        """
        super().__init__(name)
        self.clazz = clazz

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        builder.get_class(self.name).add_mixins(*self.clazz)
