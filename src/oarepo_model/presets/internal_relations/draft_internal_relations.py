#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to add the internal relations lookup-table field to the Draft class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_runtime.records.systemfields.relations import InternalRelations

from oarepo_model.customizations import (
    Customization,
    PrependMixin,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class InternalRelationsDraftLookupPreset(Preset):
    """A preset that adds an `internal_relations` lookup-table system field to the Draft class.

    Mirrors InternalRelationsLookupPreset (see record_internal_relations.py),
    but for the Draft class, so InternalRelation fields also resolve while
    editing a draft, not just on published records.

    Uses the same "only_if" pattern as DraftsUILinksPreset (see
    presets/ui_links/drafts_ui_links.py, e.g. via `only_if = ("Draft",)`) to
    skip itself gracefully when the model has no Draft class at all (i.e. no
    drafts preset was included) - internal_relations_preset is meant to be
    usable both with and without drafts.
    """

    modifies = ("Draft",)
    only_if = ("Draft",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class DraftWithInternalRelationsMixin:
            internal_relations = InternalRelations()

        yield PrependMixin(
            "Draft",
            DraftWithInternalRelationsMixin,
        )
