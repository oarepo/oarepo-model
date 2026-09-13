# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

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
    from collections.abc import Generator, Iterable

    from invenio_records_resources.services.records.params.base import ParamInterpreter

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel
from oarepo_model.customizations import (
    AddDictionary,
    PrependMixin,
)
from oarepo_model.model import Dependency, InvenioModel, ModelMixin


def resolve_params_interpreters(
    interpreters: Iterable[Any],
    extra_param_interpreter_classes: Iterable[type[ParamInterpreter]],
) -> list[Any]:
    """Replace ``FacetsParam`` by ``GroupedFacetsParam`` and insert the extra interpreters.

    The extra interpreters have to run before the facets one: the facets interpreter
    pops the whole "facets" dict from params and only puts back the entries that match
    a configured facet, so any other key living there (e.g. geo_distance:<field>)
    would be silently lost if an extra interpreter ran after it.
    """
    interpreter_classes = list(interpreters)
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
    interpreter_classes[facets_idx:facets_idx] = extra_param_interpreter_classes
    return interpreter_classes


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

        class RecordSearchOptionsMixin(ModelMixin, SearchOptions):
            facets = Dependency("RecordFacets")
            facet_groups = Dependency("FacetGroups")
            extra_param_interpreter_classes = Dependency("extra_param_interpreter_classes")

            @property
            def params_interpreters_cls(self) -> Any:
                return resolve_params_interpreters(
                    super().params_interpreters_cls,
                    self.extra_param_interpreter_classes,
                )

            query_parser_cls = staticmethod(
                QueryParser.factory(
                    tree_transformer_cls=SearchQueryValidator,
                )
            )

        yield AddList("extra_param_interpreter_classes", exists_ok=True)

        yield AddClass("RecordSearchOptions", clazz=SearchOptions)

        yield PrependMixin("RecordSearchOptions", RecordSearchOptionsMixin)
