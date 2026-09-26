# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to generate record metadata class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_db import db
from invenio_records.models import RecordMetadataBase

from oarepo_model.customizations import (
    AddBaseClass,
    AddClass,
    AddClassField,
    AddEntryPoint,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordMetadataPreset(Preset):
    """Preset for record metadata class."""

    provides = ("RecordMetadata",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass("RecordMetadata")
        yield AddBaseClass("RecordMetadata", db.Model)
        yield AddBaseClass("RecordMetadata", RecordMetadataBase)
        yield AddClassField("RecordMetadata", "__tablename__", f"{builder.model.base_name}_metadata")
        yield AddClassField("RecordMetadata", "__versioned__", {})

        yield AddEntryPoint(
            group="invenio_db.models",
            name=model.base_name,
            separator="",
            value="",
        )
