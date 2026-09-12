# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for JSON schema configuration.

This module provides the JSONSchemaPreset that configures
JSON schema modules and entry points for record validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import AddEntryPoint, AddModule, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class JSONSchemaPreset(Preset):
    """Preset that creates a jsonschemas module and adds a JSON schema entry point."""

    provides = ("jsonschemas",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddModule("jsonschemas", exists_ok=True)

        yield AddEntryPoint(
            group="invenio_jsonschemas.schemas",
            name=model.base_name,
            separator=".",
            value="jsonschemas",
        )
