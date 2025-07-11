#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddToDictionary(Customization):
    """Customization to add a value to a dictionary to the model."""

    def __init__(
        self,
        dictionary_name: str,
        *values,
        key: str | None = None,
        value: Any = None,
        exists_ok: bool = False,
    ) -> None:
        """Initialize the AddDictionary customization.

        :param name: The name of the dictionary to be added.
        :param default: The default value of the dictionary.
        :param exists_ok: Whether to ignore if the dictionary already exists.
        """
        super().__init__(dictionary_name)
        self.key = key
        self.value = value
        self.values = values
        self.exists_ok = exists_ok

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        d = builder.add_dictionary(self.name, exists_ok=True)
        for value in self.values:
            d.update(value)
        if self.key is not None:
            if self.key in d and not self.exists_ok:
                raise ValueError(
                    f"Key '{self.key}' already exists in dictionary '{self.name}'."
                )
            d[self.key] = self.value
