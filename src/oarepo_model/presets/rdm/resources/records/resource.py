"""
PLAIN_RECORD_RESOURCE = (
    "invenio_records_resources.resources.RecordResource"
)
DRAFT_RECORD_RESOURCE = (
    "invenio_drafts_resources.resources.RecordResource"
)
RDM_RECORD_RESOURCE = "oarepo_runtime.resources.resource.BaseRecordResource"

PLAIN_RESOURCE_CONFIG = (
    "invenio_records_resources.resources.RecordResourceConfig"
)
DRAFT_RESOURCE_CONFIG = "invenio_drafts_resources.resources.RecordResourceConfig"
RDM_RESOURCE_CONFIG = "oarepo_runtime.resources.config.BaseRecordResourceConfig"
"""
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

from invenio_drafts_resources.resources import RecordResource as DraftRecordResource
from invenio_records_resources.resources.records.resource import RecordResource
from oarepo_runtime.resources.resource import BaseRecordResource as RDMBaseRecordResource

from oarepo_model.customizations import ChangeBase, Customization
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class RDMRecordResourcePreset(Preset):
    """
    Preset for record resource class.
    """

    modifies = ["RecordResource"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        yield ChangeBase("RecordResource", DraftRecordResource, RDMBaseRecordResource)
