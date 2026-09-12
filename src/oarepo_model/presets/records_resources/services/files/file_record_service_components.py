# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to add FilesComponent to the list of record components."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.services.records.components import FilesComponent

from oarepo_model.customizations import AddToList, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordFilesComponent(FilesComponent):
    """Files component for record service.

    This component is given a class name so that it can be overriden in RDM.
    """


class FileRecordServiceComponentsPreset(Preset):
    """Preset for file record service components."""

    modifies = ("record_service_components",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddToList("record_service_components", RecordFilesComponent)
