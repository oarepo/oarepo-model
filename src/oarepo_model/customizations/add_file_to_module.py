#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Customization for adding files to modules.

This module provides the AddFileToModule customization that creates new files
with specified content in modules. The files can contain any text content and
are identified by symbolic names for easy reference throughout the model building
process.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddFileToModule(Customization):
    """Customization to add a property to a module to the model."""

    def __init__(
        self,
        symbolic_name: str,
        module_name: str,
        file_path: str,
        file_content: str,
        exists_ok: bool = False,  # noqa: FBT001, FBT002 - boolean argument to keep a single class
    ) -> None:
        """Initialize the AddFileToModule customization.

        :param module_name: The name of the module to be added.
        :param file_path: The path to the file to be added to the module.
        :param file_content: The content of the file to be added to the module.
        :param exists_ok: Whether to ignore if the module already exists.
        :param namespace_constant: If set, a variable with this name will be added to the module
            containing the namespace of the module and path to the file as a tuple.
        """
        super().__init__(symbolic_name)
        self.module_name = module_name
        self.file_path = file_path
        self.file_content = file_content
        self.exists_ok = exists_ok

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        builder.add_file(
            self.name,
            self.module_name,
            self.file_path,
            self.file_content,
            self.exists_ok,
        )
