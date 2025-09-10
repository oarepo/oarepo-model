#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate metadata schema for records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

import marshmallow
from oarepo_model.customizations import AddClass, AddMixins, Customization, AddList, AddToDictionary

from oarepo_model.customizations import AddClass, AddMixins, Customization
from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.services.records.record_facets import get_facets
from oarepo_model.customizations import AddModule, AddToModule, Customization
from oarepo_runtime.services.facets.utils import build_facet
if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class MetadataFacetsPreset(Preset):
    """Preset for record service class."""

    provides = ("MetadataFacets",)
    modifies = ("RecordFacets",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        if model.metadata_type is not None:

            facets = get_facets(builder, model.metadata_type)
            search_options_facets = {}
            for f in facets:
                yield AddToModule(
                "facets",
                    f,
                    build_facet(facets[f])
                )
                search_options_facets[f]= build_facet(facets[f])

            yield AddToDictionary("RecordFacets", search_options_facets)


