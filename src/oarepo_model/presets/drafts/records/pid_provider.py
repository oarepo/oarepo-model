#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for enabling draft-aware PID provider.

This module provides a preset that changes the PID provider from the standard
RecordIdProviderV2 to DraftRecordIdProviderV2, enabling proper PID management
for records that support draft functionality and versioning.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.records.api import DraftRecordIdProviderV2
from invenio_pidstore.providers.recordid_v2 import RecordIdProviderV2

from oarepo_model.customizations import ChangeBase, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class PIDProviderPreset(Preset):
    """Preset for pid provider class."""

    modifies = ("PIDProvider",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ChangeBase(
            "PIDProvider",
            RecordIdProviderV2,
            DraftRecordIdProviderV2,
        )
