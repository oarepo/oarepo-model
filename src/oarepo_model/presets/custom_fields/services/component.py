# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for adding custom fields service component support.

This module provides the CustomFieldsComponentPreset that adds
custom fields service components to record services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import AddToList, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class CustomFieldsComponentPreset(Preset):
    """Preset for record service class."""

    modifies = ("record_service_components",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        from invenio_rdm_records.services.components.custom_fields import (
            CustomFieldsComponent,
        )

        yield AddToList("record_service_components", CustomFieldsComponent)
