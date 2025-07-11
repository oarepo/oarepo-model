from oarepo_model.presets.base import Preset

from .records.draft_record import DraftRecordPreset
from .records.draft_record_metadata import DraftRecordMetadataPreset
from .records.parent_json_schema import ParentJSONSchemaPreset
from .records.parent_record import ParentRecordPreset
from .records.parent_record_metadata import ParentRecordMetadataPreset
from .records.parent_record_state import ParentRecordStatePreset
from .records.pid_provider import PIDProviderPreset
from .records.published_record_metadata_with_parent import (
    RecordMetadataWithParentPreset,
)
from .records.published_record_with_parent import RecordWithParentPreset
from .resources.records.resource import DraftRecordResourcePreset
from .resources.records.resource_config import DraftRecordResourceConfigPreset
from .services.records.service import DraftRecordServicePreset
from .services.records.service_config import DraftRecordServiceConfigPreset

drafts_records_presets: list[type[Preset]] = [
    # records layer
    ParentRecordMetadataPreset,
    DraftRecordMetadataPreset,
    RecordMetadataWithParentPreset,
    ParentRecordStatePreset,
    ParentRecordPreset,
    RecordWithParentPreset,
    DraftRecordPreset,
    ParentJSONSchemaPreset,
    PIDProviderPreset,
    # service layer
    DraftRecordServiceConfigPreset,
    DraftRecordServicePreset,
    # resource layer
    DraftRecordResourcePreset,
    DraftRecordResourceConfigPreset,
]

drafts_files_presets: list[type[Preset]] = []

drafts_presets = drafts_records_presets + drafts_files_presets
