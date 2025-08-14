#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for draft record API model.

This module provides the RDMDraftRecordPreset that changes the base class of the
record service class to RDMDraft.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.records import Draft as InvenioDraftRecord
from invenio_rdm_records.records.api import RDMDraft

from oarepo_model.customizations import ChangeBase, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMDraftRecordPreset(Preset):
    """Preset for record service class."""

    modifies = ("Draft",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ChangeBase("Draft", InvenioDraftRecord, RDMDraft)
