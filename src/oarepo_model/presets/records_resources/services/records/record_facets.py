#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate record schema class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

import marshmallow
from invenio_records_resources.services.records.schema import BaseRecordSchema

from oarepo_model.customizations import AddClass, AddMixins, Customization, AddToDictionary, AddDictionary
from oarepo_model.datatypes.collections import ObjectDataType
from oarepo_model.datatypes.strings import KeywordDataType
from oarepo_model.presets import Preset
from oarepo_model.customizations import AddModule, AddToModule, Customization

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel

from oarepo_runtime.services.facets.utils import build_facet

class RecordFacetsPreset(Preset):
    """Preset for record service class."""

    provides = ("RecordFacets",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddModule("facets")
        yield AddDictionary("RecordFacets", {})

        if model.record_type is not None:
            facets = get_facets(builder, model.metadata_type)
            search_options_facets = {}

            for f in facets:
                yield AddToModule(
                    "facets",
                    f,
                    build_facet(facets[f])
                )
                search_options_facets[f] = build_facet(facets[f])
            yield AddToDictionary("RecordFacets", search_options_facets)


def get_facets(
    builder: InvenioModelBuilder,
    schema_type: Any,
):
    """Get the marshmallow schema for a given schema type."""
    if isinstance(schema_type, (str, dict)):
        datatype = builder.type_registry.get_type(schema_type)
        return cast("Any", datatype).get_facet(
                {} if isinstance(schema_type, str) else schema_type,
            )

    # facets: type[dict[str, Any]] = {}
    # if isinstance(schema_type, KeywordDataType):
    #     datatype = builder.type_registry.get_type(schema_type)
    #     facets = cast("Any", datatype).create_facet(
    #         {} if isinstance(schema_type, str) else schema_type,
    #     )
    # # if isinstance(schema_type, (str, dict)):
    # #     datatype = builder.type_registry.get_type(schema_type)
    # #     base_schema = cast("Any", datatype).create_marshmallow_schema(
    # #         {} if isinstance(schema_type, str) else schema_type,
    # #     )
    # # elif isinstance(schema_type, ObjectDataType):
    # #     base_schema = schema_type.create_marshmallow_schema({})
    # # elif issubclass(schema_type, marshmallow.Schema):
    # #     base_schema = schema_type
    # # else:
    # #     raise TypeError(
    # #         f"Invalid schema type: {schema_type}. Expected str, dict or None.",
    # #     )
    # return facets
