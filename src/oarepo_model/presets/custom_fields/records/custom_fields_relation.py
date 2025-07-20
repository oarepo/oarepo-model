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

from invenio_vocabularies.records.systemfields.relations import CustomFieldsRelation

from oarepo_model.customizations import AddToDictionary, Customization
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class CustomFieldsRelationsPreset(Preset):

    modifies = [
        "relations",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        custom_fields_key = model.uppercase_name + "_CUSTOM_FIELDS"
        yield AddToDictionary(
            "relations",
            key=model.configuration.get("custom_fields_name", "custom"),
            value=CustomFieldsRelation(custom_fields_key),
        )
