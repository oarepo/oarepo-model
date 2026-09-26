# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to generate mappings module and entry point for records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import AddEntryPoint, AddModule, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class MappingPreset(Preset):
    """Preset that creates a mappings module and adds a mapping entry point."""

    provides = ("mappings",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddModule("mappings", exists_ok=True)

        yield AddEntryPoint(
            group="invenio_search.mappings",
            name=model.base_name,
            separator=".",
            value="mappings",
        )
