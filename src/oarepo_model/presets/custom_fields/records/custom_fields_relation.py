#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""A module for defining presets for custom fields relations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_vocabularies.records.systemfields.relations import CustomFieldsRelation

from oarepo_model.customizations import AddToDictionary, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class CustomFieldsRelationsPreset(Preset):
    """A preset that adds custom fields to the model's relation system field."""

    modifies = ("relations",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        custom_fields_key = model.uppercase_name + "_CUSTOM_FIELDS"
        yield AddToDictionary(
            "relations",
            key=model.configuration.get("custom_fields_name", "custom"),
            value=CustomFieldsRelation(custom_fields_key),
        )
