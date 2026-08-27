#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Customization for adding JSON files to modules.

This module provides the AddJSONFile customization that creates JSON files
with specified content in modules. It extends the AddFileToModule customization
by automatically serializing dictionary payloads to JSON format before adding
them to the module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddFileSymlink(Customization):
    """Customization to add a symlink to a file to the model."""

    def __init__(
        self,
        symbolic_name: str,
        module_name: str,
        file_path: str,
        exists_ok: bool = False,
    ) -> None:
        """Initialize the AddFileSymlink customization.

        :param symbolic_name: The symbolic name of the customization.
        :param module_name: The name of the module to be added.
        :param file_path: The path to the file to be added to the module.
        :param exists_ok: Whether to ignore if the module already exists.
        """
        super().__init__(symbolic_name)
        self.module_name = module_name
        self.file_path = file_path
        self.exists_ok = exists_ok

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        builder.add_symlink(
            self.name,
            self.module_name,
            self.file_path,
            self.exists_ok,
        )
