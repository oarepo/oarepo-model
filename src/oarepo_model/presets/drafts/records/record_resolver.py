#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module providing preset for draft entity resolver creation."""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, cast, override

from invenio_records_resources.references import RecordResolver as InvenioRecordResolver

from oarepo_model.customizations import (
    Customization,
    ReplaceBaseClass,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from invenio_drafts_resources.records import Draft
    from invenio_drafts_resources.services.records.service import (
        RecordService as DraftRecordService,
    )

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


# RDMRecordResolver not subclassed because the implementation is inconvenient
class DraftRecordResolver(InvenioRecordResolver):
    """Record resolver for OARepo records."""

    @override
    def matches_entity(self, entity: Any) -> bool:
        """Check if the entity is a draft or a record."""
        return isinstance(entity, (self.draft_cls, self.record_cls))

    @cached_property
    def service(self) -> DraftRecordService:
        """Get the record service."""
        return cast("DraftRecordService", self.get_service())

    @cached_property
    def draft_cls(self) -> type[Draft]:
        """Get the draft class."""
        return self.service.draft_cls  # type: ignore[no-any-return]


class DraftRecordResolverPreset(Preset):
    """Preset for draft resolver."""

    modifies = ("RecordResolver",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ReplaceBaseClass(
            "RecordResolver",
            old_base_class=InvenioRecordResolver,
            new_base_class=DraftRecordResolver,
        )
