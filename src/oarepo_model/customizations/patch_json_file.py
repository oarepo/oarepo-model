#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Customization for patching JSON files in the model.

This module provides the PatchJSONFile customization that allows modification
of existing JSON files by merging new data with the existing content. It supports
both static payloads and dynamic payloads through callable functions that receive
the current file content as input.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, override

from deepmerge import always_merger

from ..utils import dump_to_json
from .base import Customization

if TYPE_CHECKING:
    from collections.abc import Callable

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class PatchJSONFile(Customization):
    """Customization to add a JSON file to the model."""

    def __init__(
        self,
        symbolic_name: str,
        payload: dict[str, Any] | Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        """Add a json to the model.

        :param name: The name of the list to be added.
        :param exists_ok: Whether to ignore if the list already exists.
        """
        super().__init__(symbolic_name)
        self.payload = payload

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        ret = builder.get_file(self.name)
        previous_data = json.loads(ret.content)
        if callable(self.payload):
            new_data = self.payload(previous_data)
        else:
            new_data = always_merger.merge(previous_data, self.payload)
        ret.content = dump_to_json(new_data)
