#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from invenio_records.systemfields.relations import MultiRelationsField

from oarepo_model.customizations import (
    AddMixins,
    Customization,
)
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class DraftWithRelationsPreset(Preset):
    """
    Preset for Draft record with relations.

    This preset adds a MultiRelationsField to the Draft class, allowing it to
    manage multiple relations. It is similar to the RecordWithRelationsPreset
    and depends on the "relations" preset for its configuration.
    """

    modifies = [
        "Draft",
    ]

    depends_on = ["relations"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        class DraftWithRelationsMixin:
            relations = MultiRelationsField(
                **dependencies["relations"],
            )

        yield AddMixins(
            "Draft",
            DraftWithRelationsMixin,
        )
