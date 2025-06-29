#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from .api_blueprint import APIBlueprintPreset
from .app_blueprint import AppBlueprintPreset
from .ext import ExtPreset
from .proxy import ProxyPreset
from .records.dumper import RecordDumperPreset
from .records.jsonschema import JSONSchemaPreset
from .records.mapping import MappingPreset
from .records.pid_provider import PIDProviderPreset
from .records.record import RecordPreset
from .records.record_metadata import RecordMetadataPreset
from .resources.records.resource import RecordResourcePreset
from .resources.records.resource_config import RecordResourceConfigPreset
from .services.records.results import (
    RecordResultComponentsPreset,
    RecordResultItemPreset,
    RecordResultListPreset,
)
from .services.records.search_options import RecordSearchOptionsPreset
from .services.records.service import RecordServicePreset
from .services.records.service_config import RecordServiceConfigPreset

records_resources_presets = [
    # record layer
    PIDProviderPreset,
    RecordPreset,
    RecordMetadataPreset,
    RecordDumperPreset,
    JSONSchemaPreset,
    MappingPreset,
    # service layer
    RecordServicePreset,
    RecordServiceConfigPreset,
    RecordResultComponentsPreset,
    RecordResultItemPreset,
    RecordResultListPreset,
    RecordSearchOptionsPreset,
    # resource layer
    RecordResourcePreset,
    RecordResourceConfigPreset,
    # extension
    ExtPreset,
    ProxyPreset,
    APIBlueprintPreset,
    AppBlueprintPreset,
]
