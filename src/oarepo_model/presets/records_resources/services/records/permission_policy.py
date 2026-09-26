# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to generate permission policy class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_runtime.services.config import EveryonePermissionPolicy

from oarepo_model.customizations import AddClass, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class PermissionPolicyPreset(Preset):
    """Preset for record service class."""

    provides = ("PermissionPolicy",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass("PermissionPolicy", clazz=EveryonePermissionPolicy)
