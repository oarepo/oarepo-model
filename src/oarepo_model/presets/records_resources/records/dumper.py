# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for record dumper functionality.

This module provides the DumperPreset that configures
record dumpers for converting records to search-friendly formats.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records.dumpers import SearchDumper as InvenioSearchDumper

from oarepo_model.customizations import (
    AddClass,
    AddList,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


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
        yield AddClass("RecordDumper", clazz=InvenioSearchDumper)
        yield AddList("record_dumper_extensions")
