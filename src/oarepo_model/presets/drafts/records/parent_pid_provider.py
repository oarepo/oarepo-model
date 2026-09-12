# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to generate parent PID provider class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.records.api import DraftRecordIdProviderV2
from invenio_records_resources.records.systemfields.pid import PIDField, PIDFieldContext
from oarepo_runtime.records.pid_providers import UniversalPIDMixin

from oarepo_model.customizations import AddClass, Customization, PrependMixin
from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.records.pid_provider import make_pid_type

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class ParentPIDProviderPreset(Preset):
    """Preset for parent pid provider class."""

    provides = (
        "ParentPIDProvider",
        "ParentPIDField",
        "ParentPIDFieldContext",
    )

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class PIDProviderMixin:
            pid_type = builder.model.configuration.get("parent_pid_type") or make_pid_type(
                builder.model.base_name,
            )

        yield AddClass("ParentPIDProvider", clazz=DraftRecordIdProviderV2)
        yield PrependMixin("ParentPIDProvider", PIDProviderMixin)
        yield PrependMixin("ParentPIDProvider", UniversalPIDMixin)

        yield AddClass("ParentPIDField", clazz=PIDField)
        yield AddClass("ParentPIDFieldContext", clazz=PIDFieldContext)
