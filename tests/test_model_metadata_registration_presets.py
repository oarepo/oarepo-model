#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from oarepo_model.api import model
from oarepo_model.presets.records_resources.model_registration import (
    ModelMetadataRegistrationPreset,
    ModelRegistrationPreset,
)


def test_model_metadata_registration_presets(
    app,
):
    m = model(
        name="metadata_load_test_with_model_metadata_registration_presets",
        version="1.0.0",
        presets=[
            ModelRegistrationPreset,
            ModelMetadataRegistrationPreset,
        ],
        types=[
            {
                "RecordMetadata": {"properties": {"title": {"type": "TitleType"}}},
                "TitleType": {
                    "type": "fulltext+keyword",
                },
            },
        ],
        metadata_type="RecordMetadata",
    )

    assert m.oarepo_model_arguments["model_metadata"].record_type is None
    assert m.oarepo_model_arguments["model_metadata"].metadata_type == "RecordMetadata"
    assert m.oarepo_model_arguments["model_metadata"].types == {
        "multilingual": {"type": "multilingual-type", "items": {"type": "i18n"}},
        "i18n": {
            "type": "object",
            "properties": {
                "lang": {
                    "type": "vocabulary",
                    "vocabulary-type": "languages",
                    "searchable": False,
                },
                "value": {"type": "keyword", "searchable": False},
            },
        },
        "RecordMetadata": {"properties": {"title": {"type": "TitleType"}}},
        "TitleType": {"type": "fulltext+keyword"},
    }
