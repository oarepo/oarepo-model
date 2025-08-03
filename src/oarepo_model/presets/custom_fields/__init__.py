#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Custom fields presets for OARepo models.

This package provides presets for adding custom fields functionality to OARepo models,
including support for extensible record schemas and dynamic field configurations.
"""

from __future__ import annotations

from .records.api import RecordWithCustomFieldsPreset
from .records.custom_fields_relation import CustomFieldsRelationsPreset
from .records.draft import DraftWithCustomFieldsPreset
from .records.draft_mapping import CustomFieldsDraftMappingPreset
from .records.jsonschema import CustomFieldsJSONSchemaPreset
from .records.mapping import CustomFieldsMappingPreset
from .services.component import CustomFieldsComponentPreset
from .services.schema import RecordCustomFieldsSchemaPreset

custom_fields_presets = [
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
]
