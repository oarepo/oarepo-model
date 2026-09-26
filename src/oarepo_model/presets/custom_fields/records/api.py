# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Record with custom fields preset."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records.systemfields import DictField

from oarepo_model.customizations import Customization, PrependMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordWithCustomFieldsPreset(Preset):
    """Preset for adding custom fields to the Record model.

    This preset modifies the Record model to include a custom_fields system field.
    """

    modifies = ("Record",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class RecordWithCustomFieldsMixin:
            #: Custom fields system field.
            custom_fields = DictField(clear_none=True, create_if_missing=True)

        yield PrependMixin("Record", RecordWithCustomFieldsMixin)
