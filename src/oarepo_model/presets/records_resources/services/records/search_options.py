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

import inspect
from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.services.records.config import SearchOptions
from invenio_records_resources.services.records.params.facets import FacetsParam
from invenio_records_resources.services.records.queryparser import QueryParser
from oarepo_runtime.services.facets.params import GroupedFacetsParam
from oarepo_runtime.services.queryparsers.transformer import (
    SearchQueryValidator,
)

from oarepo_model.customizations import AddClass, AddList, Customization
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

    provides = ("RecordSearchOptions", "extra_param_interpreter_classes")

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
            extra_param_interpreter_classes = Dependency("extra_param_interpreter_classes")

            @property
            def params_interpreters_cls(self) -> Any:
                interpreter_classes = super().params_interpreters_cls  # type: ignore[misc]
                # make a copy of the list
                interpreter_classes = list(interpreter_classes)
                # replace FacetsParam with GroupedFacetsParam
                facets_idx = None
                for idx, clazz in enumerate(interpreter_classes):
                    if inspect.isclass(clazz) and issubclass(clazz, FacetsParam):
                        interpreter_classes[idx] = GroupedFacetsParam
                        facets_idx = idx
                        break
                if facets_idx is None:
                    # could not find, insert at the start
                    interpreter_classes.insert(0, GroupedFacetsParam)
                    facets_idx = 0
                # Extra interpreters must run before the facets interpreter: the
                # facets interpreter pops the whole "facets" dict from params and
                # only puts back the entries that match a configured facet, so
                # any other key living there (e.g. geo_distance:<field>) would be
                # silently lost if an extra interpreter ran after it.
                interpreter_classes[facets_idx:facets_idx] = self.extra_param_interpreter_classes
                return interpreter_classes

            query_parser_cls = staticmethod(
                QueryParser.factory(
                    tree_transformer_cls=SearchQueryValidator,
                )
            )

        yield AddList("extra_param_interpreter_classes", exists_ok=True)

        yield AddClass("RecordSearchOptions", clazz=SearchOptions)

        yield PrependMixin("RecordSearchOptions", RecordSearchOptionsMixin)
