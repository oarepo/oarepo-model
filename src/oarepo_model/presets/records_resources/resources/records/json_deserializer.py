# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""UI JSON serializer preset for Invenio record resources.

This module provides a preset that creates a JSON serializer specifically designed
for user interface contexts. It includes:

- JSONDeserializerPreset: A preset that provides the JSONDeserializer class
- JSONDeserializer: A deserializer that uses the RecordUISchema
  for object serialization and outputs JSON format with UI-specific context
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from flask_resources import JSONDeserializer

from oarepo_model.customizations import AddClass, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class JSONDeserializerPreset(Preset):
    """Preset for JSON Deserializer."""

    provides = ("JSONDeserializer",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass("JSONDeserializer", JSONDeserializer)
