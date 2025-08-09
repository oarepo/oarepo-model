#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Customization for copying files between locations in the model.

This module provides the CopyFile customization that allows copying content
from one symbolic file location to another within the model builder. This is
useful for duplicating configuration files or templates across different
modules or locations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class CopyFile(Customization):
    """Customization to copy a file from one location to another."""

    def __init__(
        self,
        source_symbolic_name: str,
        target_symbolic_name: str,
        target_module_name: str,
        target_file_path: str,
        exists_ok: bool = False,  # noqa: FBT002 - boolean argument to keep a single class
    ) -> None:
        """Add a json to the model.

        :param name: The name of the list to be added.
        :param exists_ok: Whether to ignore if the list already exists.
        """
        super().__init__(source_symbolic_name)
        self.target_symbolic_name = target_symbolic_name
        self.target_module_name = target_module_name
        self.target_file_path = target_file_path
        self.exists_ok = exists_ok

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        source = builder.get_file(self.name)
        builder.add_file(
            self.target_symbolic_name,
            self.target_module_name,
            self.target_file_path,
            source.content,
            self.exists_ok,
        )
