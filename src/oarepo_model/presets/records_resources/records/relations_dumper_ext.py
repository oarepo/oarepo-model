# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to generate record dumper extensions for relations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records.dumpers.relations import RelationDumperExt

from oarepo_model.customizations import AddToList, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RelationsDumperExtPreset(Preset):
    """Preset that adds a RelationDumperExt to the record dumper extensions."""

    modifies = ("record_dumper_extensions",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddToList(
            "record_dumper_extensions",
            RelationDumperExt("relations"),
        )
