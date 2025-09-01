#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from oarepo_model.api import FunctionalPreset, model
from oarepo_model.presets.records_resources import (
    MetadataSchemaPreset,
    RecordSchemaPreset,
)


def test_functional_presets_called(
    app,
):
    mock = MagicMock()

    class MockFunctionalPreset(FunctionalPreset):
        def __getattribute__(self, name: str) -> Any:
            return getattr(mock, name)

    model(
        name="metadata_load_test_with_functional_presets",
        version="1.0.0",
        presets=[
            [
                RecordSchemaPreset,
                MetadataSchemaPreset,
                FunctionalPreset,
                MockFunctionalPreset,
            ],
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

    assert mock.before_invenio_model.called
    assert mock.before_populate_type_registry.called
    assert mock.after_populate_type_registry.called
    assert mock.after_builder_created.called
    assert mock.after_presets_sorted.called
    assert mock.after_user_customizations_applied.called
    assert mock.after_model_built.called
