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
from typing import TYPE_CHECKING, Any, Callable, override

from deepmerge import always_merger

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class PatchJSONFile(Customization):
    """Customization to add a JSON file to the model."""

    def __init__(
        self,
        module_name: str,
        file_path: str,
        payload: dict[str, Any] | Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        """Add a json to the model

        :param name: The name of the list to be added.
        :param exists_ok: Whether to ignore if the list already exists.
        """
        super().__init__(module_name + "/" + file_path)
        self.module_name = module_name
        self.file_path = file_path
        self.payload = payload

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        ret = builder.get_file(self.module_name, self.file_path)
        previous_data = json.loads(ret.content)
        if callable(self.payload):
            new_data = self.payload(previous_data)
        else:
            new_data = always_merger.merge(previous_data, self.payload)
        ret.content = json.dumps(new_data)
