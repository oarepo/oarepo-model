# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Customization for adding base classes to OARepo model components.

This module provides the AddBaseClass customization that allows adding base classes
to existing classes in an OARepo model during the building process.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddBaseClass(Customization):
    """Customization to add base classes to a model class.

    This customization allows you to add one or more base classes to an existing
    class in the model with a specified name and class types.
    """

    def __init__(self, name: str, clazz: type) -> None:
        """Initialize the AddBaseClass customization.

        :param name: The name of the class to add base classes to.
        :param clazz: The base class type(s) to be added.
        """
        super().__init__(name)
        self.clazz = clazz

    modifies_own_name = True

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        builder.get_class(self.name).add_base_classes(self.clazz)
