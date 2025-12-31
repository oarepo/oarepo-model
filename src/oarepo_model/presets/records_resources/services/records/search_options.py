#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate record search options class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.services.records.config import SearchOptions
from invenio_records_resources.services.records.params.facets import FacetsParam
from oarepo_runtime.services.facets.params import GroupedFacetsParam

from oarepo_model.customizations import AddClass, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel
from oarepo_model.customizations import (
    AddDictionary,
    PrependMixin,
)
from oarepo_model.model import Dependency, InvenioModel, ModelMixin


class RecordSearchOptionsPreset(Preset):
    """Preset for record search options class."""

    provides = ("RecordSearchOptions",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddDictionary("FacetGroups", {}, exists_ok=True)

        class RecordSearchOptionsMixin(ModelMixin):
            facets = Dependency("RecordFacets")
            facet_groups = Dependency("FacetGroups")

            @property
            def params_interpreters_cls(self) -> Any:
                interpreter_classes = super().params_interpreters_cls  # type: ignore[reportAttributeAccessIssue]
                # make a copy of the list
                interpreter_classes = list(interpreter_classes)
                # replace FacetsParam with GroupedFacetsParam
                for idx, clazz in enumerate(interpreter_classes):
                    if issubclass(clazz, FacetsParam):
                        interpreter_classes[idx] = GroupedFacetsParam
                        break
                else:
                    # could not find, insert at the start
                    interpreter_classes.insert(0, GroupedFacetsParam)
                return interpreter_classes

        yield AddClass("RecordSearchOptions", clazz=SearchOptions)

        yield PrependMixin("RecordSearchOptions", RecordSearchOptionsMixin)
