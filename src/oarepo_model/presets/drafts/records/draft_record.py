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

from invenio_drafts_resources.records import Draft as InvenioDraft
from invenio_rdm_records.records.systemfields import HasDraftCheckField
from invenio_records.systemfields import ConstantField
from invenio_records_resources.records.systemfields import IndexField
from oarepo_runtime.records.systemfields.record_status import RecordStatusSystemField

from oarepo_model.customizations import (
    AddClass,
    AddMixins,
    Customization,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class DraftPreset(Preset):
    """
    Preset for Draft record.
    """

    depends_on = [
        "RecordMetadata",
        "PIDField",
        "PIDProvider",
        "PIDFieldContext",
    ]

    provides = [
        "Draft",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        class DraftMixin:
            """Base class for records in the model.
            This class extends InvenioRecord and can be customized further.
            """

            model_cls = Dependency("DraftMetadata")
            versions_model_cls = Dependency("ParentRecordState")
            parent_record_cls = Dependency("ParentRecord")

            schema = ConstantField(
                "$schema",
                f"local://{builder.model.base_name}-v1.0.0.json",
            )

            index = IndexField(
                f"{builder.model.base_name}-draft-metadata-v1.0.0",
                search_alias=f"{builder.model.base_name}",
            )

            pid = dependencies["PIDField"](
                provider=dependencies["PIDProvider"],
                context_cls=dependencies["PIDFieldContext"],
                create=True,
                delete=False,
            )

            dumper = Dependency(
                "RecordDumper", transform=lambda RecordDumper: RecordDumper()
            )

            # note: we need to use the has_draft field from rdm records
            # even if this is the draft record - unfortunately the system field
            # is defined in the invenio-rdm-records package
            has_draft = HasDraftCheckField()

            # TODO: remove this field - note that we need to change the implementation
            # if the RecordList to use "is_draft" instead of "record_status"
            record_status = RecordStatusSystemField()

        yield AddClass(
            "Draft",
            clazz=InvenioDraft,
        )
        yield AddMixins(
            "Draft",
            DraftMixin,
        )
