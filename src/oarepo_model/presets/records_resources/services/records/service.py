# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to generate record service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.services.records.service import RecordService
from oarepo_runtime.services.config.components import ComponentsOrderingMixin

from oarepo_model.customizations import AddClass, Customization, PrependMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordServicePreset(Preset):
    """Preset for record service class."""

    provides = ("RecordService",)
    modifies = ("oarepo_model_arguments",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass("RecordService", clazz=RecordService)
        yield PrependMixin("RecordService", ComponentsOrderingMixin)
