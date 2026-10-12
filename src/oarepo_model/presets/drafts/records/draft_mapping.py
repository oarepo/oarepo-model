# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for draft record Opensearch mapping configuration.

This module provides the DraftMappingPreset that configures
Opensearch mappings for draft records in Invenio applications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import CopyFile, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftMappingPreset(Preset):
    """Preset for creating draft record Opensearch mapping configuration."""

    depends_on = ("record-mapping",)
    provides = ("draft-mapping",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield CopyFile(
            source_symbolic_name="record-mapping",
            target_symbolic_name="draft-mapping",
            target_module_name="mappings",
            target_file_path=f"os-v2/{model.base_name}/draft-metadata-v{model.version}.json",
        )
