#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Record with custom fields preset."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records.systemfields import DictField

from oarepo_model.customizations import AddMixins, Customization
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

        yield AddMixins("Record", RecordWithCustomFieldsMixin)
