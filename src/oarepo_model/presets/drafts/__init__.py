from oarepo_model.presets.base import Preset

from .blueprints.files.api_draft_files_blueprint import ApiDraftFilesBlueprintPreset
from .blueprints.files.api_draft_media_files_blueprint import (
    ApiDraftMediaFilesBlueprintPreset,
)
from .blueprints.files.api_media_files_blueprint import ApiMediaFilesBlueprintPreset
from .ext_draft_files import ExtDraftFilesPreset
from .ext_draft_media_files import ExtDraftMediaFilesPreset
from .ext_media_files import ExtMediaFilesPreset
from .file_records.draft_file_mapping import DraftFileMappingPreset
from .file_records.draft_media_files import DraftMediaFilesPreset
from .file_records.draft_with_files import DraftWithFilesPreset
from .file_records.draft_with_media_files import DraftWithMediaFilesPreset
from .file_records.file_draft import FileDraftPreset
from .file_records.file_draft_metadata import FileDraftMetadataPreset
from .file_records.media_file_draft import MediaFileDraftPreset
from .file_records.media_file_draft_metadata import MediaFileDraftMetadataPreset
from .file_records.media_file_metadata import MediaFileMetadataPreset
from .file_records.media_file_record import MediaFileRecordPreset
from .file_records.record_media_files import RecordMediaFilesPreset
from .file_records.record_with_media_files import RecordWithMediaFilesPreset
from .records.draft_mapping import DraftMappingPreset
from .records.draft_record import DraftPreset
from .records.draft_record_metadata import DraftMetadataPreset
from .records.parent_record import ParentRecordPreset
from .records.parent_record_metadata import ParentRecordMetadataPreset
from .records.parent_record_state import ParentRecordStatePreset
from .records.pid_provider import PIDProviderPreset
from .records.published_record_metadata_with_parent import (
    RecordMetadataWithParentPreset,
)
from .records.published_record_with_parent import RecordWithParentPreset
from .resources.files.draft_file_resource import DraftFileResourcePreset
from .resources.files.draft_file_resource_config import DraftFileResourceConfigPreset
from .resources.files.draft_media_file_resource import DraftMediaFileResourcePreset
from .resources.files.draft_media_file_resource_config import (
    DraftMediaFileResourceConfigPreset,
)
from .resources.files.media_file_resource import MediaFileResourcePreset
from .resources.files.media_file_resource_config import MediaFileResourceConfigPreset
from .resources.records.resource import DraftResourcePreset
from .resources.records.resource_config import DraftResourceConfigPreset
from .services.files.draft_file_record_service_components import (
    DraftFileRecordServiceComponentsPreset,
)
from .services.files.draft_file_service import DraftFileServicePreset
from .services.files.draft_file_service_config import DraftFileServiceConfigPreset
from .services.files.draft_media_file_service import DraftMediaFileServicePreset
from .services.files.draft_media_file_service_config import (
    DraftMediaFileServiceConfigPreset,
)
from .services.files.media_file_service import MediaFileServicePreset
from .services.files.media_file_service_config import MediaFileServiceConfigPreset
from .services.files.media_files_record_service_components import (
    FileRecordServiceComponentsPreset,
)
from .services.files.media_files_record_service_config import (
    MediaFilesRecordServiceConfigPreset,
)
from .services.files.no_upload_file_service_config import (
    NoUploadFileServiceConfigPreset,
)
from .services.records.record_schema import DraftRecordSchemaPreset
from .services.records.service import DraftServicePreset
from .services.records.service_config import DraftServiceConfigPreset

drafts_records_presets: list[type[Preset]] = [
    # records layer
    ParentRecordMetadataPreset,
    DraftMetadataPreset,
    RecordMetadataWithParentPreset,
    ParentRecordStatePreset,
    ParentRecordPreset,
    RecordWithParentPreset,
    DraftPreset,
    PIDProviderPreset,
    DraftMappingPreset,
    # service layer
    DraftServiceConfigPreset,
    DraftServicePreset,
    DraftRecordSchemaPreset,
    # resource layer
    DraftResourcePreset,
    DraftResourceConfigPreset,
]

drafts_files_presets: list[type[Preset]] = [
    # records layer
    MediaFileRecordPreset,
    MediaFileDraftPreset,
    FileDraftPreset,
    RecordWithMediaFilesPreset,
    RecordMediaFilesPreset,
    DraftWithFilesPreset,
    DraftWithMediaFilesPreset,
    DraftMediaFilesPreset,
    MediaFileMetadataPreset,
    MediaFileDraftMetadataPreset,
    FileDraftMetadataPreset,
    # record layer
    DraftFileMappingPreset,
    # service layer
    MediaFilesRecordServiceConfigPreset,
    DraftFileRecordServiceComponentsPreset,
    FileRecordServiceComponentsPreset,
    DraftFileServiceConfigPreset,
    NoUploadFileServiceConfigPreset,
    MediaFileServiceConfigPreset,
    DraftMediaFileServiceConfigPreset,
    DraftFileServicePreset,
    DraftMediaFileServicePreset,
    MediaFileServicePreset,
    # resource layer
    DraftFileResourceConfigPreset,
    DraftFileResourcePreset,
    MediaFileResourceConfigPreset,
    MediaFileResourcePreset,
    DraftMediaFileResourceConfigPreset,
    DraftMediaFileResourcePreset,
    # ext
    ExtDraftFilesPreset,
    ExtMediaFilesPreset,
    ExtDraftMediaFilesPreset,
    # blueprints
    ApiDraftFilesBlueprintPreset,
    ApiMediaFilesBlueprintPreset,
    ApiDraftMediaFilesBlueprintPreset,
]

drafts_presets = drafts_records_presets + drafts_files_presets
