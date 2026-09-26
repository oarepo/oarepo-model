# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for creating draft media file resource.

This module provides a preset that creates a DraftMediaFileResource class
based on Invenio's FileResource. This resource provides REST API endpoints
for accessing media files attached to draft records.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.resources import FileResource

from oarepo_model.customizations import AddClass, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftMediaFileResourcePreset(Preset):
    """Preset for file resource class."""

    provides = ("DraftMediaFileResource",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass("DraftMediaFileResource", FileResource)
