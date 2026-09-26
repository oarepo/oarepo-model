# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Custom fields presets for OARepo models.

This package provides presets for adding custom fields functionality to OARepo models,
including support for extensible record schemas and dynamic field configurations.
"""

from __future__ import annotations

from .ext import CustomFieldsFeaturePreset
from .records.api import RecordWithCustomFieldsPreset
from .records.custom_fields_relation import CustomFieldsRelationsPreset
from .records.draft import DraftWithCustomFieldsPreset
from .records.draft_mapping import CustomFieldsDraftMappingPreset
from .records.jsonschema import CustomFieldsJSONSchemaPreset
from .records.mapping import CustomFieldsMappingPreset
from .services.component import CustomFieldsComponentPreset
from .services.schema import RecordCustomFieldsSchemaPreset

custom_fields_preset = [
    # records layer
    RecordWithCustomFieldsPreset,
    CustomFieldsRelationsPreset,
    DraftWithCustomFieldsPreset,
    CustomFieldsMappingPreset,
    CustomFieldsDraftMappingPreset,
    CustomFieldsJSONSchemaPreset,
    # services layer
    RecordCustomFieldsSchemaPreset,
    CustomFieldsComponentPreset,
    # feature
    CustomFieldsFeaturePreset,
]
