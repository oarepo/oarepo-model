#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for adding draft file components to record service.

This module provides a preset that adds DraftFilesComponent and DraftMediaFilesComponent
to the record service components list. These components enable file and media file
handling in draft-enabled record services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.services.records.components import (
    DraftFilesComponent,
    DraftMediaFilesComponent,
)

from oarepo_model.customizations import AddToList, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftFileRecordServiceComponentsPreset(Preset):
    """Preset for file record service components."""

    modifies = ("record_service_components",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddToList("record_service_components", DraftFilesComponent)
        yield AddToList("record_service_components", DraftMediaFilesComponent)
