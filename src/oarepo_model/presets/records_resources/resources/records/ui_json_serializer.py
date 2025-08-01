#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from flask_resources import BaseListSchema, MarshmallowSerializer
from flask_resources.serializers import JSONSerializer

from oarepo_model.customizations import AddClass, Customization
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class JSONUISerializerPreset(Preset):
    """
    Preset for UI JSON Serializer.
    """

    provides = ["JSONUISerializer"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        runtime_dependencies = builder.get_runtime_dependencies()
                

        class JSONUISerializer(MarshmallowSerializer):
            """UI JSON serializer."""

            def __init__(self):
                """Initialise Serializer."""
                super().__init__(
                    format_serializer_cls=JSONSerializer,
                    object_schema_cls=runtime_dependencies.get("RecordUISchema"),
                    list_schema_cls=BaseListSchema,
                    schema_context={"object_key": "ui"},
                )
        
        yield AddClass("JSONUISerializer", JSONUISerializer)        
                