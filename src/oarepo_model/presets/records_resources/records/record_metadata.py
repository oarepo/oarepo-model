#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate record metadata class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, override

from invenio_db import db
from invenio_records.models import RecordMetadataBase

from oarepo_model.customizations import (
    AddBaseClasses,
    AddClass,
    AddEntryPoint,
    AddMixins,
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
        class RecordMetadataMixin:
            __tablename__ = f"{builder.model.base_name}_metadata"
            __table_args__: ClassVar[dict[str, Any]] = {"extend_existing": True}
            __versioned__: ClassVar[dict[Any, Any]] = {}

        yield AddClass("RecordMetadata")
        yield AddBaseClasses("RecordMetadata", db.Model, RecordMetadataBase)
        yield AddMixins("RecordMetadata", RecordMetadataMixin)
        yield AddEntryPoint(
            group="invenio_db.models",
            name=model.base_name,
            separator="",
            value="",
        )
