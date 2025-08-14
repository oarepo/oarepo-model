# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for creating RDM record resource config.

This module provides a preset that modifies record resource config to RDM compatibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.resources import (
    RecordResourceConfig as DraftRecordResourceConfig,
)
from invenio_rdm_records.resources.config import RDMRecordResourceConfig as RDMBaseRecordResourceConfig

# TODO: from oarepo_runtime.resources.config import BaseRecordResourceConfig as RDMBaseRecordResourceConfig
from oarepo_model.customizations import (
    ChangeBase,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMRecordResourceConfigPreset(Preset):
    """Preset for record resource config class."""

    modifies = ("RecordResourceConfig",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ChangeBase("RecordResourceConfig", DraftRecordResourceConfig, RDMBaseRecordResourceConfig)
