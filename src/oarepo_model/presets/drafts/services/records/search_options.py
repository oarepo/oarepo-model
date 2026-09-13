# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to generate record search options class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.services.records.config import SearchDraftsOptions
from invenio_records_resources.services.records.queryparser import QueryParser
from oarepo_runtime.services.queryparsers.transformer import (
    SearchQueryValidator,
)

from oarepo_model.customizations import AddClass, AddDictionary, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


from oarepo_model.customizations import (
    PrependMixin,
)
from oarepo_model.model import Dependency, InvenioModel, ModelMixin
from oarepo_model.presets.records_resources.services.records.search_options import (
    resolve_params_interpreters,
)


class DraftSearchOptionsPreset(Preset):
    """Preset for record search options class."""

    provides = ("DraftSearchOptions",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddDictionary("DraftFacetGroups", {}, exists_ok=True)

        class DraftSearchOptionsMixin(ModelMixin, SearchDraftsOptions):
            facets = Dependency("RecordFacets")
            facet_groups = Dependency("DraftFacetGroups")
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

        yield AddClass("DraftSearchOptions", clazz=SearchDraftsOptions)

        yield PrependMixin("DraftSearchOptions", DraftSearchOptionsMixin)
