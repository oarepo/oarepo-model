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
from typing import TYPE_CHECKING, Any, Generator

from oarepo_model.customizations import (
    AddFileToModule,
    Customization,
)
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class ParentJSONSchemaPreset(Preset):
    """
    Adds parent JSON schema to the model.
    """

    provides = [
        "parent_json_schema",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        yield AddFileToModule(
            "jsonschemas",
            "parent-v1.0.0.json",
            json.dumps(
                {
                    "$schema": "http://json-schema.org/draft-07/schema#",
                    "$id": "local://parent-v1.0.0.json",
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                }
            ),
        )
