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

from typing import Any

from ..utils import dump_to_json
from .add_file_to_module import AddFileToModule


class AddJSONFile(AddFileToModule):
    """Customization to add a JSON file to the model."""

    def __init__(
        self,
        symbolic_name: str,
        module_name: str,
        file_path: str,
        payload: dict[str, Any],
        exists_ok: bool = False,  # noqa: FBT002 - boolean argument to keep a single class
    ) -> None:
        """Add a json to the model.

        :param name: The name of the list to be added.
        :param exists_ok: Whether to ignore if the list already exists.
        """
        super().__init__(
            symbolic_name=symbolic_name,
            module_name=module_name,
            file_path=file_path,
            file_content=dump_to_json(payload),
            exists_ok=exists_ok,
        )
