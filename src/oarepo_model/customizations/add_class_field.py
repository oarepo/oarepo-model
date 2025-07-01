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


class AddClassField(Customization):
    """Customization to add a field to the model.

    This customization allows you to add a field to the model
    with a specified name and value.
    """

    def __init__(self, name: str, field_name: str, field_value: Any) -> None:
        """Initialize the AddClassField customization.

        :param name: The name of the class to be modified.
        :param field_name: The name of the field to be added.
        :param field_value: The value of the field to be added.
        """
        super().__init__(name)
        self.field_name = field_name
        self.field_value = field_value

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        builder.get_class(self.name).fields[self.field_name] = self.field_value
