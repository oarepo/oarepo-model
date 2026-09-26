# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for adding custom fields support to draft records.

This module provides the DraftWithCustomFieldsPreset that adds
custom fields capability to draft record classes in Invenio.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records.systemfields import DictField

from oarepo_model.customizations import (
    Customization,
    PrependMixin,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftWithCustomFieldsPreset(Preset):
    """Preset for Draft record with custom fields."""

    modifies = ("Draft",)

    # build only if Draft will be built as well
    only_if = ("Draft",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class DraftWithCustomFieldsMixin:
            #: Custom fields system field.
            custom_fields = DictField(clear_none=True, create_if_missing=True)

        yield PrependMixin("Draft", DraftWithCustomFieldsMixin)
