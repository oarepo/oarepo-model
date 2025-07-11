#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from invenio_drafts_resources.records.api import DraftRecordIdProviderV2
from invenio_pidstore.providers.recordid_v2 import RecordIdProviderV2

from oarepo_model.customizations import ChangeBase, Customization
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class PIDProviderPreset(Preset):
    """
    Preset for pid provider class
    """

    modifies = [
        "PIDProvider",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        yield ChangeBase(
            "PIDProvider",
            RecordIdProviderV2,
            DraftRecordIdProviderV2,
        )
