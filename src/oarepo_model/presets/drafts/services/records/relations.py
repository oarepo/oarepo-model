# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for adding relations support to draft-enabled record services.

This module provides a preset that adds the RelationsComponent to the record
service components list. This component enables proper handling of relationships
between records in a draft-enabled environment.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.services.records.components import (
    RelationsComponent,
)

from oarepo_model.customizations import (
    AddToList,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RelationsServiceComponentPreset(Preset):
    """Preset for relations service component."""

    modifies = ("record_service_components",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddToList("record_service_components", RelationsComponent)
