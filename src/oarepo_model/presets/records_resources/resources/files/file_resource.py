# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module to generate file resource class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.resources import FileResource

from oarepo_model.customizations import AddClass, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class FileResourcePreset(Preset):
    """Preset for file resource class."""

    provides = ("FileResource",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass("FileResource", FileResource)
