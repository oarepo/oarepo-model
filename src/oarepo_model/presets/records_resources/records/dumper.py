#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for record dumper functionality.

This module provides the DumperPreset that configures
record dumpers for converting records to search-friendly formats.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_runtime.records.dumpers import SearchDumper
from oarepo_runtime.records.systemfields.mapping import SystemFieldDumperExt

from oarepo_model.customizations import (
    AddClass,
    AddList,
    AddMixins,
    AddToList,
    Customization,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder


class RecordDumperPreset(Preset):
    """Preset for record dumper class."""

    provides = ("RecordDumper", "record_dumper_extensions")

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class RecordDumperMixin:
            extensions = Dependency(
                "record_dumper_extensions",
                default=[],
            )

        yield AddClass("RecordDumper", clazz=SearchDumper)
        yield AddMixins("RecordDumper", RecordDumperMixin)
        yield AddList("record_dumper_extensions")

        # TODO: remove this when we review oarepo-runtime
        yield AddToList(
            "record_dumper_extensions",
            SystemFieldDumperExt(),
        )
