#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for creating parent record API class.

This module provides a preset that creates a ParentRecord class based on
Invenio's ParentRecord API. The parent record manages relationships between
different versions of a record and provides a stable identifier for the
conceptual record across its lifecycle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.records import ParentRecord as InvenioParentRecord
from invenio_records.systemfields import ConstantField

from oarepo_model.customizations import (
    AddClass,
    AddMixins,
    Customization,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder


class ParentRecordPreset(Preset):
    """Preset that creates a ParentRecord class."""

    provides = ("ParentRecord",)

    depends_on = (
        "PIDField",
        "PIDProvider",
        "PIDFieldContext",
    )

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class ParentRecordMixin:
            """Base class for parent records in the model."""

            model_cls = Dependency("ParentRecordMetadata")

            schema = ConstantField(
                "$schema",
                "local://records/parent-v3.0.0.json",
            )

            pid = dependencies["PIDField"](
                provider=dependencies["PIDProvider"],
                context_cls=dependencies["PIDFieldContext"],
                create=True,
                delete=True,
            )

        yield AddClass(
            "ParentRecord",
            clazz=InvenioParentRecord,
        )
        yield AddMixins(
            "ParentRecord",
            ParentRecordMixin,
        )
