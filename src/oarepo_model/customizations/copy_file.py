#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class CopyFile(Customization):
    """Customization to copy a file from one location to another."""

    def __init__(
        self,
        source_module_name: str,
        source_file_path: str,
        target_module_name: str,
        target_file_path: str,
        exists_ok: bool = False,
        namespace_constant: str | None = None,
    ) -> None:
        """Add a json to the model

        :param name: The name of the list to be added.
        :param exists_ok: Whether to ignore if the list already exists.
        """
        super().__init__(target_module_name)
        self.source_module_name = source_module_name
        self.source_file_path = source_file_path
        self.target_module_name = target_module_name
        self.target_file_path = target_file_path
        self.exists_ok = exists_ok
        self.namespace_constant = namespace_constant

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        source_module = builder.get_module(self.source_module_name)
        source_base_directory = source_module.__file__
        if not source_base_directory.endswith("/__init__.py"):
            raise ValueError(
                f"Source module '{self.source_module_name}' does not have a valid file path."
            )
        source_pth = Path(source_base_directory).parent / self.source_file_path
        if not source_pth.exists():
            raise FileNotFoundError(
                f"Source file '{self.source_file_path}' does not exist in module '{self.source_module_name}'."
            )

        target_module = builder.get_module(self.target_module_name)
        target_base_directory = target_module.__file__
        if not target_base_directory.endswith("/__init__.py"):
            raise ValueError(
                f"Target module '{self.target_module_name}' does not have a valid file path."
            )
        target_pth = Path(target_base_directory).parent / self.target_file_path
        if target_pth.exists() and not self.exists_ok:
            raise FileExistsError(
                f"Target file '{self.target_file_path}' already exists in module '{self.target_module_name}'."
            )
        target_pth.parent.mkdir(parents=True, exist_ok=True)

        shutil.copyfile(source_pth, target_pth)

        if self.namespace_constant:
            builder.add_constant(
                self.namespace_constant,
                (self.target_module_name, self.target_file_path),
            )
