#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for creating RDM record service config.

This module provides a preset that modifies record service config to RDM compatibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.services import RecordServiceConfig as DraftRecordServiceconfig
from invenio_rdm_records.services.config import RDMRecordServiceConfig

# TODO: from oarepo_runtime.services.config.service import SearchAllConfigMixin
from oarepo_model.customizations import ChangeBase, Customization
from oarepo_model.presets import Preset

"""
PLAIN_RECORD_SERVICE = (
    "invenio_records_resources.services.RecordService{InvenioRecordService}"
)
DRAFT_RECORD_SERVICE = (
    "invenio_drafts_resources.services.RecordService{InvenioRecordService}"
)
RDM_RECORD_SERVICE = "oarepo_runtime.services.service.SearchAllRecordsService"

PLAIN_SERVICE_CONFIG = (
    "invenio_records_resources.services.RecordServiceConfig{InvenioRecordServiceConfig}"
)
DRAFT_SERVICE_CONFIG = "invenio_drafts_resources.services.RecordServiceConfig{InvenioRecordDraftsServiceConfig}"
RDM_SERVICE_CONFIG = "invenio_rdm_records.services.config.RDMRecordServiceConfig"
"""


if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMRecordServiceConfigPreset(Preset):
    """Preset for record service class."""

    modifies = ("RecordServiceConfig",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ChangeBase("RecordServiceConfig", DraftRecordServiceconfig, RDMRecordServiceConfig)
        # TODO: yield AddMixins("RecordServiceConfig", SearchAllConfigMixin)
