#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Customization for adding mixins to OARepo model classes.

This module provides the PrependMixin customization that allows adding mixin classes
to existing classes in an OARepo model during the building process.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class PrependMixin(Customization):
    """Customization to add mixins to a model class.

    This customization allows you to add one or more mixin classes to an existing
    class in the model with a specified name and class types.
    """

    def __init__(self, name: str, clazz: type) -> None:
        """Initialize the PrependMixin customization.

        :param name: The name of the class to add mixins to.
        :param clazz: The mixin class type(s) to be added.
        """
        super().__init__(name)
        self.clazz = clazz

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        builder.get_class(self.name).add_mixins(self.clazz)
