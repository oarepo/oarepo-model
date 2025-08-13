#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Customization for creating new dictionaries in the model.

This module provides the AddDictionary customization that creates new dictionaries
with specified names and optional default values in the model builder. These
dictionaries can be used to collect key-value pairs and configuration data
during the model building process.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddDictionary(Customization):
    """Customization to add a dictionary to the model.

    A dictionary is a collection of key-value pairs that will be added to the model.
    """

    def __init__(
        self,
        name: str,
        default: dict[str, Any] | None = None,
        exists_ok: bool = False,
    ) -> None:
        """Initialize the AddDictionary customization.

        :param name: The name of the dictionary to be added.
        :param default: The default value of the dictionary.
        :param exists_ok: Whether to ignore if the dictionary already exists.
        """
        super().__init__(name)
        self.default = default
        self.exists_ok = exists_ok

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        builder.add_dictionary(self.name, self.default, exists_ok=self.exists_ok)
