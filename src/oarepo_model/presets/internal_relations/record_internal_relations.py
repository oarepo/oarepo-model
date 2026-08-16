#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to add the internal relations lookup-table field to the Record class."""

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


class InternalRelationsLookupPreset(Preset):
    """A preset that adds an `internal_relations` lookup-table system field to the Record class.

    `InternalRelations` (see oarepo_runtime.records.systemfields.relations)
    needs no configuration - it auto-discovers every dict with an "id" field
    anywhere in the record and exposes it under `record.internal_relations`,
    keyed by its own dot-separated path. `InternalRelationDataType` fields
    (see datatypes/internal_relations.py) resolve against this lookup table at
    runtime, so this preset is required for them to actually work, not just
    build.
    """

    modifies = ("Record",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class RecordWithInternalRelationsMixin:
            internal_relations = InternalRelations()

        yield PrependMixin(
            "Record",
            RecordWithInternalRelationsMixin,
        )
