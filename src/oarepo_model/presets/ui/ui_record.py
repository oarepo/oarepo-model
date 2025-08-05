#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""A module for generating ui.json for Jinja components and JavaScript."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from oarepo_model.customizations import AddDictionary, Customization
from oarepo_model.datatypes.collections import ObjectDataType
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class UIRecordPreset(Preset):
    """Preset generating UI schema for Jinja components and javascript."""

    provides = ("ui",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        """Apply the preset to the model and yield customizations."""
        record_ui_model = get_ui_model(builder, model.record_type, [])

        yield AddDictionary("ui_model", record_ui_model)


def get_ui_model(
    builder: InvenioModelBuilder,
    schema_type: Any,
    initial_path: list[str],
) -> dict[str, Any]:
    """Get the UI model for a given schema type."""
    base_schema: dict[str, Any] = {}
    if isinstance(schema_type, (str, dict)):
        datatype = builder.type_registry.get_type(schema_type)
        base_schema = cast("Any", datatype).create_ui_model(
            {} if isinstance(schema_type, str) else schema_type,
            path=initial_path,
        )
    elif isinstance(schema_type, ObjectDataType):
        base_schema = schema_type.create_ui_model({}, path=initial_path)
    else:
        raise TypeError(
            f"Invalid schema type: {schema_type}. Expected str, dict or None.",
        )
    return base_schema
