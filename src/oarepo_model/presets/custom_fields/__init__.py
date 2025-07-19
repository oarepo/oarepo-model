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
