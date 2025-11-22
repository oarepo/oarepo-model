#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for enabling draft support in record resource.

This module provides a preset that changes the base record resource from
RecordResource to DraftResource, enabling REST API endpoints for draft
operations like create, edit, publish, and delete drafts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.resources import RecordResource as DraftResource
from invenio_records_resources.resources.records.resource import RecordResource

from oarepo_model.customizations import Customization, ReplaceBaseClass
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftResourcePreset(Preset):
    """Preset for record resource class."""

    modifies = ("RecordResource",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ReplaceBaseClass("RecordResource", RecordResource, DraftResource)
