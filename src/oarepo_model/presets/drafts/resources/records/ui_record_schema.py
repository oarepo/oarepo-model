#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Draft record UI schema extensions for Invenio record serialization.

This module provides UI schema extensions specifically for draft records. It includes:

- DraftRecordUISchemaMixin: A mixin class that adds draft-specific fields to the UI schema,
  including an is_draft boolean field with proper formatting
- DraftsRecordUISchemaPreset: A preset that modifies the base RecordUISchema to include
  draft-specific functionality
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import Customization, PrependMixin
from oarepo_model.datatypes.boolean import FormatBoolean
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftRecordUISchemaMixin:
    """Mixin for draft record UI schema which adds is_draft field."""

    is_draft = FormatBoolean(attribute="is_draft")


class DraftsRecordUISchemaPreset(Preset):
    """Preset for draft service class."""

    modifies = ("RecordUISchema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield PrependMixin("RecordUISchema", DraftRecordUISchemaMixin)
