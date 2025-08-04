#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for adding parent record support to published record metadata.

This module provides a preset that extends the RecordMetadata model with
parent record functionality by adding the ParentRecordMixin base class
and establishing the relationship to the parent record metadata model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.records import (
    ParentRecordMixin,
)
from sqlalchemy.orm import declared_attr

from oarepo_model.customizations import (
    AddBaseClasses,
    AddMixins,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordMetadataWithParentPreset(Preset):
    """Preset for record metadata class."""

    modifies = ("RecordMetadata",)
    depends_on = ("ParentRecordMetadata",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class ParentRecordModelMixin:
            @declared_attr
            def __parent_record_model__(cls):  # noqa declared attr is a class method
                return dependencies["ParentRecordMetadata"]

        yield AddBaseClasses("RecordMetadata", ParentRecordMixin)
        yield AddMixins("RecordMetadata", ParentRecordModelMixin)
