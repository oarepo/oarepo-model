#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for configuring draft-enabled record resource.

This module provides a preset that changes the base record resource configuration
from RecordResourceConfig to DraftResourceConfig, providing the necessary
configuration for draft-enabled REST API endpoints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.resources import (
    RecordResourceConfig as DraftResourceConfig,
)
from invenio_records_resources.resources.records.config import RecordResourceConfig

from oarepo_model.customizations import (
    Customization,
    ReplaceBaseClass,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftResourceConfigPreset(Preset):
    """Preset for record resource config class."""

    modifies = ("RecordResourceConfig",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ReplaceBaseClass(
            "RecordResourceConfig",
            RecordResourceConfig,
            DraftResourceConfig,
        )
