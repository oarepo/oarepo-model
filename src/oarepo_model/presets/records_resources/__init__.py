#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from .blueprints.blueprint_module import BlueprintModulePreset
from .blueprints.files.api_blueprint import ApiFilesBlueprintPreset
from .blueprints.records.api_blueprint import ApiBlueprintPreset
from .blueprints.records.app_blueprint import AppBlueprintPreset
from .ext import ExtPreset
from .ext_files import ExtFilesPreset
from .file_records.file_metadata import FileMetadataPreset
from .file_records.file_record import FileRecordPreset
from .file_records.record import RecordWithFilesPreset
from .file_records.record_metadata import RecordMetadataWithFilesPreset
from .proxy import ProxyPreset
from .records.dumper import RecordDumperPreset
from .records.jsonschema import JSONSchemaPreset
from .records.mapping import MappingPreset
from .records.metadata_json_schema import MetadataJSONSchemaPreset
from .records.metadata_mapping import MetadataMappingPreset
from .records.pid_provider import PIDProviderPreset
from .records.record import RecordPreset
from .records.record_json_schema import RecordJSONSchemaPreset
from .records.record_mapping import RecordMappingPreset
from .records.record_metadata import RecordMetadataPreset
from .resources.files.file_resource import FileResourcePreset
from .resources.files.file_resource_config import FileResourceConfigPreset
from .resources.records.resource import RecordResourcePreset
from .resources.records.resource_config import RecordResourceConfigPreset
from .services.files.file_record_service_components import (
    FileRecordServiceComponentsPreset,
)
from .services.files.file_service import FileServicePreset
from .services.files.file_service_config import FileServiceConfigPreset
from .services.files.record_with_files_schema import (
    RecordWithFilesSchemaPreset,
)
from .services.records.metadata_schema import MetadataSchemaPreset
from .services.records.permission_policy import PermissionPolicyPreset
from .services.records.record_schema import RecordSchemaPreset
from .services.records.results import (
    RecordResultComponentsPreset,
    RecordResultItemPreset,
    RecordResultListPreset,
)
from .services.records.search_options import RecordSearchOptionsPreset
from .services.records.service import RecordServicePreset
from .services.records.service_config import RecordServiceConfigPreset

records_presets = [
    # record layer
    PIDProviderPreset,
    RecordPreset,
    RecordMetadataPreset,
    RecordDumperPreset,
    JSONSchemaPreset,
    MappingPreset,
    RecordJSONSchemaPreset,
    MetadataJSONSchemaPreset,
    RecordMappingPreset,
    MetadataMappingPreset,
    # service layer
    RecordServicePreset,
    RecordServiceConfigPreset,
    RecordResultComponentsPreset,
    RecordResultItemPreset,
    RecordResultListPreset,
    RecordSearchOptionsPreset,
    PermissionPolicyPreset,
    RecordSchemaPreset,
    MetadataSchemaPreset,
    # resource layer
    RecordResourcePreset,
    RecordResourceConfigPreset,
    # extension
    ExtPreset,
    ProxyPreset,
    BlueprintModulePreset,
    ApiBlueprintPreset,
    AppBlueprintPreset,
]

files_presets = [
    # file layer
    FileRecordPreset,
    RecordWithFilesPreset,
    RecordMetadataWithFilesPreset,
    FileMetadataPreset,
    # service layer
    FileRecordServiceComponentsPreset,
    FileServiceConfigPreset,
    FileServicePreset,
    RecordWithFilesSchemaPreset,
    # resource layer
    FileResourcePreset,
    FileResourceConfigPreset,
    # extension
    ExtFilesPreset,
    ApiFilesBlueprintPreset,
]

records_resources_presets = records_presets + files_presets
