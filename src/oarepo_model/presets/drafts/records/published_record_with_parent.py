#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for enabling parent record support in published records.

This module provides a preset that extends published records with parent record
functionality, enabling versioning and draft capabilities. It adds system fields
for tracking draft status and record status, and establishes relationships
with parent records and version models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.records import Record as DraftBase
from invenio_rdm_records.records.systemfields import HasDraftCheckField
from invenio_records_resources.records import Record as RecordBase
from oarepo_runtime.records.systemfields import PublicationStatusSystemField

from oarepo_model.customizations import Customization, PrependMixin, ReplaceBaseClass
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder


class RecordWithParentPreset(Preset):
    """Preset for enabling parent record support in published records."""

    modifies = ("Record",)

    depends_on = ("Draft",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class ParentRecordMixin:
            versions_model_cls = Dependency("ParentRecordState")
            parent_record_cls = Dependency("ParentRecord")

            # note: we need to use the has_draft field from rdm records
            # even if this is the draft record - unfortunately the system field
            # is defined in the invenio-rdm-records package
            has_draft = HasDraftCheckField(dependencies["Draft"])

            publication_status = PublicationStatusSystemField()

        yield ReplaceBaseClass("Record", RecordBase, DraftBase, subclass=True)
        yield PrependMixin("Record", ParentRecordMixin)
