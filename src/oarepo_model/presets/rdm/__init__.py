from oarepo_model.presets.rdm.ext import RDMExtPreset
from oarepo_model.presets.rdm.records.draft_record import RDMDraftRecordPreset
from oarepo_model.presets.rdm.records.draft_record_metadata import RDMDraftRecordMetadataWithFilesPreset
from oarepo_model.presets.rdm.records.parent_record import RDMParentRecordPreset
from oarepo_model.presets.rdm.records.rdm_mapping import RDMMappingPreset
from oarepo_model.presets.rdm.records.record import RDMRecordPreset
from oarepo_model.presets.rdm.records.record_metadata import RDMRecordMetadataWithFilesPreset
from oarepo_model.presets.rdm.resources.records.resource import RDMRecordResourcePreset
from oarepo_model.presets.rdm.resources.records.resource_config import RDMRecordResourceConfigPreset
from oarepo_model.presets.rdm.services.records.record_schema import RDMRecordSchemaPreset
from oarepo_model.presets.rdm.services.records.service import RDMRecordServicePreset
from oarepo_model.presets.rdm.services.records.service_config import RDMRecordServiceConfigPreset

rdm_presets = [RDMMappingPreset,
               RDMDraftRecordPreset,
               RDMParentRecordPreset,
               RDMRecordPreset, RDMRecordResourcePreset, RDMRecordResourceConfigPreset,
               RDMRecordServicePreset,
               RDMRecordServiceConfigPreset, RDMDraftRecordMetadataWithFilesPreset, RDMRecordMetadataWithFilesPreset,
               RDMExtPreset,
               RDMRecordSchemaPreset]