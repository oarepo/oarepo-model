#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for adding custom fields support to draft record mappings.

This module provides the CustomFieldsDraftMappingPreset that adds
custom fields mapping configuration to draft records in Elasticsearch.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import Customization, PatchJSONFile
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class CustomFieldsDraftMappingPreset(Preset):
    """Preset for adding custom fields to draft record mappings."""

    modifies = ("draft-mapping",)
    only_if = ("draft-mapping",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        file_mapping = {
            "mappings": {
                "properties": {
                    "custom_fields": {
                        "type": "object",
                        "dynamic": True,
                    },
                },
            },
        }

        yield PatchJSONFile(
            "draft-mapping",
            file_mapping,
        )
