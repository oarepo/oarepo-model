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

from invenio_drafts_resources.records import (
    ParentRecordMixin,
)
from sqlalchemy.orm import declared_attr

from oarepo_model.customizations import (
    AddBaseClasses,
    AddMixins,
    Customization,
)
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class RecordMetadataWithParentPreset(Preset):
    """
    Preset for record metadata class
    """

    modifies = [
        "RecordMetadata",
    ]
    depends_on = [
        "ParentRecordMetadata",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        class ParentRecordModelMixin:
            @declared_attr
            def __parent_record_model__(cls):
                return dependencies["ParentRecordMetadata"]

        yield AddBaseClasses("RecordMetadata", ParentRecordMixin)
        yield AddMixins("RecordMetadata", ParentRecordModelMixin)
