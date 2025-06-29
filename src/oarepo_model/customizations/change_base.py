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

from oarepo_model.errors import BaseClassNotFoundError

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class ChangeBase(Customization):
    """Customization to change the base class of a model.

    This customization allows you to change the base class of a model
    with a specified name and class type.
    """

    def __init__(
        self,
        name: str,
        old_base_class: type,
        new_base_class: type,
        fail: bool = True,
        subclass: bool = False,
    ) -> None:
        """Initialize the ChangeBase customization.

        :param name: The name of the mixin to be added.
        :param clazz: The class type to be added.
        """
        super().__init__(name)
        self.old_base_class = old_base_class
        self.new_base_class = new_base_class
        self.fail = fail
        self.subclass = subclass

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        clz = builder.get_class(self.name)
        for idx, base in enumerate(clz.base_classes):
            if (
                self.old_base_class is base
                or self.subclass
                and issubclass(base, self.old_base_class)
            ):
                clz.base_classes[idx] = self.new_base_class
                break
        else:
            if self.fail:
                raise BaseClassNotFoundError(
                    f"Base class {self.old_base_class.__name__} not found in {self.name} base classes {clz.base_classes}."
                )
            else:
                return
