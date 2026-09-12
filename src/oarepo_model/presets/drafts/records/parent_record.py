# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

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
    Customization,
    PrependMixin,
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
        "ParentPIDField",
        "ParentPIDProvider",
        "ParentPIDFieldContext",
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

            pid = dependencies["ParentPIDField"](
                provider=dependencies["ParentPIDProvider"],
                context_cls=dependencies["ParentPIDFieldContext"],
                create=True,
                delete=True,
            )

        yield AddClass(
            "ParentRecord",
            clazz=InvenioParentRecord,
        )
        yield PrependMixin(
            "ParentRecord",
            ParentRecordMixin,
        )
