# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for adding draft file components to record service.

This module provides a preset that adds DraftFilesComponent and DraftMediaFilesComponent
to the record service components list. These components enable file and media file
handling in draft-enabled record services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.services.records.components import (
    DraftFilesComponent as InvenioDraftFilesComponent,
)
from invenio_drafts_resources.services.records.components import (
    DraftMediaFilesComponent as InvenioDraftMediaFilesComponent,
)

from oarepo_model.customizations import AddToList, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftFilesComponent(InvenioDraftFilesComponent):
    """Files component for record service.

    This component is given a class name so that it can be overriden in RDM.
    """


class DraftMediaFilesComponent(InvenioDraftMediaFilesComponent):
    """Media files component for record service.

    This component is given a class name so that it can be overriden in RDM.
    """


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
