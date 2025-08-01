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


class AddBaseClasses(Customization):
    """Customization to add a base class to the model.

    This customization allows you to add a base class to the model
    with a specified name and class type.
    """

    def __init__(self, name: str, *clazz: type) -> None:
        """Initialize the AddBaseClasses customization.

        :param name: The name of the base class to be added.
        :param clazz: The class type to be added.
        """
        super().__init__(name)
        self.clazz = clazz

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        builder.get_class(self.name).base_classes.extend(self.clazz)
