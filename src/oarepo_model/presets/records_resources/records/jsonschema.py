#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
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
