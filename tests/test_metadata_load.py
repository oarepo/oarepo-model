# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

import marshmallow as ma
import pytest
from marshmallow import Schema

from oarepo_model.api import model
from oarepo_model.presets.records_resources import (
    MetadataSchemaPreset,
    RecordSchemaPreset,
)


def test_metadata_load_from_dict(
    app,
):
    m = model(
        name="metadata_load_test",
        version="1.0.0",
        presets=[
            [
                RecordSchemaPreset,
                MetadataSchemaPreset,
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

    assert issubclass(m.RecordSchema, Schema)
    assert m.RecordSchema().load(
        {
            "metadata": {
                "title": "Test Title",
            },
        },
    ) == {
        "metadata": {
            "title": "Test Title",
        },
    }


@pytest.fixture(
    scope="module",
    params=[
        "model_types_in_json",
        "model_types_in_json_with_origin",
        "model_types_in_yaml",
        "model_types_in_yaml_with_origin",
    ],
)
def model_with_loaded_types(request, app):
    """Model whose datatypes come from json/yaml files (dict and list format), absolute or origin-relative."""
    return model(
        name="model_types_load_test",
        version="1.0.0",
        presets=[
            [
                RecordSchemaPreset,
                MetadataSchemaPreset,
            ],
        ],
        types=[
            {
                "RecordMetadata": {
                    "properties": {
                        "article": {"type": "article"},
                        "comment": {"type": "comment"},
                        "creator": {"type": "creator"},
                        "person": {"type": "person"},
                    },
                },
            },
            *request.getfixturevalue(request.param),
        ],
        metadata_type="RecordMetadata",
    )


@pytest.mark.parametrize(
    "metadata",
    [
        pytest.param({"person": {"id": 0, "name": "Bob", "age": 123}}, id="person"),
        pytest.param({"creator": {"id": 0, "handles": ["1", "2", "3"], "active": True}}, id="creator"),
        pytest.param(
            {
                "article": {"id": 0, "title": "Bob in a Jungle", "tags": ["tag1", "tag2"]},
                "comment": {
                    "id": 1,
                    "article_id": 1,
                    "content": "Comment",
                    "author": {"name": "Bob", "age": 123},
                },
            },
            id="article+comment",
        ),
    ],
)
def test_loaded_datatypes_accept_valid_metadata(model_with_loaded_types, metadata):
    valid_metadata = {"metadata": metadata}
    assert model_with_loaded_types.RecordSchema().load(valid_metadata) == valid_metadata


@pytest.mark.parametrize(
    "metadata",
    [
        pytest.param({"person": {"id": "1", "name": "Bob", "age": 123}}, id="person-id-not-int"),
        pytest.param(
            {"creator": {"id": 0, "handles": ["1", "2", "3"], "active": "not bool"}},
            id="creator-active-not-bool",
        ),
        pytest.param({"article": {"id": "1"}}, id="article-id-not-int"),
        pytest.param({"comment": {"id": "1"}}, id="comment-id-not-int"),
    ],
)
def test_loaded_datatypes_reject_invalid_metadata(model_with_loaded_types, metadata):
    with pytest.raises(ma.exceptions.ValidationError):
        model_with_loaded_types.RecordSchema().load({"metadata": metadata})
