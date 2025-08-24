#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for record exports."""

from __future__ import annotations

from oarepo_runtime import current_runtime


def test_runtime_model(
    app,
    rdm_model,
):
    runtime_model = current_runtime.models["rdm_test"]
    assert runtime_model.code == "rdm_test"
    assert str(runtime_model.name) == "rdm_test"
    assert runtime_model.version == "1.0.0"
    assert str(runtime_model.description) == ""
    assert runtime_model.records_alias_enabled is True
    assert len(runtime_model.ui_model) > 0
    assert isinstance(runtime_model.service, rdm_model.RecordService)
    assert isinstance(runtime_model.service_config, rdm_model.RecordServiceConfig)
    assert runtime_model.record_cls is rdm_model.Record
    assert runtime_model.draft_cls is rdm_model.Draft
    assert isinstance(runtime_model.file_service, rdm_model.FileService)
    assert isinstance(runtime_model.draft_file_service, rdm_model.DraftFileService)
    assert isinstance(runtime_model.media_file_service, rdm_model.MediaFileService)
    assert isinstance(runtime_model.media_draft_file_service, rdm_model.DraftMediaFileService)
    assert runtime_model.record_pid_type == "rdmtst"
    assert runtime_model.record_json_schema == "local://rdm_test-v1.0.0.json"

    assert runtime_model.draft_pid_type == "rdmtst"

    assert runtime_model.api_url("search") == "https://127.0.0.1:5000/api/rdm-test"

    assert isinstance(runtime_model.resource_config, rdm_model.RecordResourceConfig)
    assert isinstance(runtime_model.resource, rdm_model.RecordResource)

    assert {exp.code for exp in runtime_model.exports} == {"json", "ui_json"}
    assert runtime_model.response_handlers.keys() == {
        "application/json",
        "application/vnd.inveniordm.v1+json",
    }
