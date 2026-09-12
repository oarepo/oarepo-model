# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for creating draft record metadata model.

This module provides a preset that creates a DraftMetadata database model
for storing draft record information. It includes the DraftMetadataBase
and ParentRecordMixin to enable proper draft functionality and parent
record relationships.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_db import db
from invenio_drafts_resources.records import (
    DraftMetadataBase,
    ParentRecordMixin,
)

from oarepo_model.customizations import (
    AddBaseClass,
    AddClass,
    AddClassField,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftMetadataPreset(Preset):
    """Preset for draft record metadata class."""

    provides = ("DraftMetadata",)
    depends_on = ("ParentRecordMetadata",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass("DraftMetadata")
        yield AddClassField(
            "DraftMetadata",
            "__tablename__",
            f"{builder.model.base_name}_draft_metadata",
        )
        yield AddClassField(
            "DraftMetadata",
            "__parent_record_model__",
            dependencies["ParentRecordMetadata"],
        )
        yield AddBaseClass("DraftMetadata", db.Model)
        yield AddBaseClass("DraftMetadata", DraftMetadataBase)
        yield AddBaseClass("DraftMetadata", ParentRecordMixin)
