#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""A module for defining presets for model relations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from oarepo_model.datatypes.collections import ObjectDataType
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.customizations import Customization
    from oarepo_model.model import InvenioModel


class RecordRelationsPreset(Preset):
    """Preset for generating relations for records."""

    modifies = ("relations",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        _dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        """Apply the preset to the model and yield customizations."""
        if model.metadata_type is not None:
            yield from get_relations_fields(
                builder,
                model.metadata_type,
                [
                    ("metadata", {"type": "object"}),
                ],
            )
        if model.record_type is not None:
            yield from get_relations_fields(builder, model.record_type, [])


def get_relations_fields(
    builder: InvenioModelBuilder,
    schema_type: Any,
    path: list[tuple[str, dict[str, Any]]],
) -> Generator[Customization]:
    """Get the relations fields for a given record type."""
    if isinstance(schema_type, (str, dict)):
        datatype = builder.type_registry.get_type(schema_type)
        yield from cast("Any", datatype).create_relations(
            {} if isinstance(schema_type, str) else schema_type,
            path,
        )
    elif isinstance(schema_type, ObjectDataType):
        yield from schema_type.create_relations({}, path)
    else:
        raise TypeError(
            f"Invalid schema type: {schema_type}. Expected str, dict or None.",
        )
