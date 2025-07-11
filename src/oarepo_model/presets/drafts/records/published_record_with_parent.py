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

from invenio_drafts_resources.records import Record as DraftRecordBase
from invenio_rdm_records.records.systemfields import HasDraftCheckField
from invenio_records_resources.records import Record as RecordBase
from oarepo_runtime.records.systemfields.record_status import RecordStatusSystemField

from oarepo_model.customizations import AddMixins, ChangeBase, Customization
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class RecordWithParentPreset(Preset):

    modifies = [
        "Record",
    ]

    depends_on = ["DraftRecord"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        class ParentRecordMixin:
            versions_model_cls = Dependency("ParentRecordState")
            parent_record_cls = Dependency("ParentRecord")

            # note: we need to use the has_draft field from rdm records
            # even if this is the draft record - unfortunately the system field
            # is defined in the invenio-rdm-records package
            has_draft = HasDraftCheckField(dependencies["DraftRecord"])

            # TODO: remove this field - note that we need to change the implementation
            # if the RecordList to use "is_draft" instead of "record_status"
            record_status = RecordStatusSystemField()

        yield ChangeBase("Record", RecordBase, DraftRecordBase, subclass=True)
        yield AddMixins("Record", ParentRecordMixin)
