#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from .add_file_to_module import AddFileToModule

if TYPE_CHECKING:
    pass


class AddJSONFile(AddFileToModule):
    """Customization to add a JSON file to the model."""

    def __init__(
        self,
        symbolic_name: str,
        module_name: str,
        file_path: str,
        payload: dict[str, Any],
        exists_ok: bool = False,
    ) -> None:
        """Add a json to the model

        :param name: The name of the list to be added.
        :param exists_ok: Whether to ignore if the list already exists.
        """
        super().__init__(
            symbolic_name=symbolic_name,
            module_name=module_name,
            file_path=file_path,
            file_content=json.dumps(payload),
            exists_ok=exists_ok,
        )
