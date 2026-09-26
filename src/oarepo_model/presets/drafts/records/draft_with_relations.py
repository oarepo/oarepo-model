# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for adding relations support to draft records.

This module provides a preset that adds a MultiRelationsField to the Draft
class, enabling draft records to manage relationships with other records.
This is essential for maintaining referential integrity during the draft
editing process.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records.systemfields.relations import MultiRelationsField

from oarepo_model.customizations import (
    Customization,
    PrependMixin,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftWithRelationsPreset(Preset):
    """Preset for Draft record with relations.

    This preset adds a MultiRelationsField to the Draft class, allowing it to
    manage multiple relations. It is similar to the RecordWithRelationsPreset
    and depends on the "relations" preset for its configuration.
    """

    modifies = ("Draft",)

    depends_on = ("relations",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class DraftWithRelationsMixin:
            relations = MultiRelationsField(
                **dependencies["relations"],
            )

        yield PrependMixin(
            "Draft",
            DraftWithRelationsMixin,
        )
