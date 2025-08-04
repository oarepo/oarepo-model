#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to add multi-relations field to the Record class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records.systemfields.relations import MultiRelationsField

from oarepo_model.customizations import (
    AddMixins,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordWithRelationsPreset(Preset):
    """A preset that adds a MultiRelationsField to the Record class.

    This preset modifies the Record class by introducing a relations field
    using MultiRelationsField. The relations field is configured based on
    dependencies provided during the application of the preset.
    """

    modifies = ("Record",)

    depends_on = ("relations",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class RecordWithRelationsMixin:
            relations = MultiRelationsField(
                **dependencies["relations"],
            )

        yield AddMixins(
            "Record",
            RecordWithRelationsMixin,
        )
