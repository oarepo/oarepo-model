#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""UI JSON serializer preset for Invenio record resources.

This module provides a preset that creates a JSON serializer specifically designed
for user interface contexts. It includes:

- DefaultRDMUISerializerPreset: A preset that provides the DefaultRDMUISerializer class
- DefaultRDMUISerializer: A Marshmallow-based serializer that uses the RecordUISchema
  for object serialization and outputs JSON format with UI-specific context
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from flask_resources import BaseListSchema, MarshmallowSerializer
from flask_resources.serializers import JSONSerializer
from oarepo_runtime.resources.serializers.rdm import DefaultRDMUISchema

from oarepo_model.customizations import AddClass, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DefaultRDMUISerializerPreset(Preset):
    """Preset for UI JSON Serializer."""

    provides = ("DefaultRDMUISerializer",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        runtime_dependencies = builder.get_runtime_dependencies()

        class DefaultRDMUISerializer(MarshmallowSerializer):
            """UI JSON serializer."""

            def __init__(self):
                """Initialise Serializer."""
                super().__init__(
                    format_serializer_cls=JSONSerializer,
                    object_schema_cls=DefaultRDMUISchema,
                    list_schema_cls=BaseListSchema,
                )

        yield AddClass("DefaultRDMUISerializer", DefaultRDMUISerializer)
