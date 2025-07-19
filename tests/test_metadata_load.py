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
            ]
        ],
        types=[
            {
                "RecordMetadata": {"properties": {"title": {"type": "TitleType"}}},
                "TitleType": {
                    "type": "fulltext+keyword",
                },
            }
        ],
        metadata_type="RecordMetadata",
    )

    assert issubclass(m.RecordSchema, Schema)
    assert m.RecordSchema().load(
        {
            "metadata": {
                "title": "Test Title",
            }
        }
    ) == {
        "metadata": {
            "title": "Test Title",
        },
    }
