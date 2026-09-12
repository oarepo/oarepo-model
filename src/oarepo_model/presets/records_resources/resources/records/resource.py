# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to generate record resource class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.resources.records.resource import RecordResource

from oarepo_model.customizations import AddClass, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordResourcePreset(Preset):
    """Preset for record resource class."""

    provides = ("RecordResource",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass("RecordResource", RecordResource)
