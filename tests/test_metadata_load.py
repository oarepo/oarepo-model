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


def test_load_datatypes_from_json(app, model_types_in_json, model_types_in_json_with_origin, search_clear):
    m = model(
        name="model_types_load_test_from_json",
        version="1.0.0",
        presets=[
            [
                RecordSchemaPreset,
                MetadataSchemaPreset,
            ]
        ],
        types=[
            {
                "RecordMetadata": {
                    "properties": {
                        "article": {"type": "article"},
                        "comment": {"type": "comment"},
                        "creator": {"type": "creator"},
                        "person": {"type": "person"},
                    }
                },
            }
        ]
        + model_types_in_json,
        metadata_type="RecordMetadata",
    )
    assert issubclass(m.RecordSchema, Schema)
    
    m2 = model(
        name="model_types_load_test_from_json",
        version="1.0.0",
        presets=[
            [
                RecordSchemaPreset,
                MetadataSchemaPreset,
            ]
        ],
        types=[
            {
                "RecordMetadata": {
                    "properties": {
                        "article": {"type": "article"},
                        "comment": {"type": "comment"},
                        "creator": {"type": "creator"},
                        "person": {"type": "person"},
                    }
                },
            }
        ]
        + model_types_in_json_with_origin,
        metadata_type="RecordMetadata",
    )
    assert issubclass(m.RecordSchema, Schema)
    

    # loaded from json in dictionary format
    valid_metadata = {"metadata": {"person": {"id": 0, "name": "Bob", "age": 123}}}
    assert m.RecordSchema().load(valid_metadata) == valid_metadata
    assert m2.RecordSchema().load(valid_metadata) == valid_metadata
    
    # loaded from json in dictionary format
    valid_metadata = {"metadata": {"creator": {"id": 0, "handles": ["1", "2","3"], "active": True}}}
    assert m.RecordSchema().load(valid_metadata) == valid_metadata
    assert m2.RecordSchema().load(valid_metadata) == valid_metadata
    
    # loaded from json in array format
    valid_metadata = {
        "metadata": {
            "article": {"id": 0, "title": "Bob in a Jungle", "tags": ["tag1", "tag2"]},
            "comment": {
                "id": 1,
                "article_id": 1,
                "content": "Comment",
                "author": {"name": "Bob", "age": 123},
            },
        }
    }
    assert m.RecordSchema().load(valid_metadata) == valid_metadata
    assert m2.RecordSchema().load(valid_metadata) == valid_metadata
    
    invalid_metadata = {
        "metadata": {
            "person": {
                "id": "1",  # should be int
                "name": "Bob",
                "age": 123,
            }
        }
    }
    with pytest.raises(ma.exceptions.ValidationError):
        m.RecordSchema().load(invalid_metadata)
    with pytest.raises(ma.exceptions.ValidationError):
        m2.RecordSchema().load(invalid_metadata)
    
    
    invalid_metadata = {"metadata": {"creator": {"id": 0, "handles": ["1", "2","3"], "active": "not bool"}}}
    with pytest.raises(ma.exceptions.ValidationError):
        m.RecordSchema().load(invalid_metadata)
    with pytest.raises(ma.exceptions.ValidationError):
        m2.RecordSchema().load(invalid_metadata)
    
    invalid_metadata = {
        "metadata": {
            "article": {
                "id": "1",  # should be int
            }
        }
    }
    with pytest.raises(ma.exceptions.ValidationError):
        m.RecordSchema().load(invalid_metadata)    
    with pytest.raises(ma.exceptions.ValidationError):
        m2.RecordSchema().load(invalid_metadata)
        
    invalid_metadata = {
        "metadata": {
            "comment": {
                "id": "1",  # should be int
            }
        }
    }
    with pytest.raises(ma.exceptions.ValidationError):
        m.RecordSchema().load(invalid_metadata)     
    with pytest.raises(ma.exceptions.ValidationError):
        m2.RecordSchema().load(invalid_metadata)    


def test_load_datatypes_from_yaml(app, model_types_in_yaml, model_types_in_yaml_with_origin, search_clear):
    m = model(
        name="model_types_load_test_from_yaml",
        version="1.0.0",
        presets=[
            [
                RecordSchemaPreset,
                MetadataSchemaPreset,
            ]
        ],
        types=[
            {
                "RecordMetadata": {
                    "properties": {
                        "article": {"type": "article"},
                        "comment": {"type": "comment"},
                        "person": {"type": "person"},
                        "creator": {"type": "creator"}
                    }
                },
            }
        ]
        + model_types_in_yaml,
        metadata_type="RecordMetadata",
    )
    assert issubclass(m.RecordSchema, Schema)

    m2 = model(
        name="model_types_load_test_from_yaml",
        version="1.0.0",
        presets=[
            [
                RecordSchemaPreset,
                MetadataSchemaPreset,
            ]
        ],
        types=[
            {
                "RecordMetadata": {
                    "properties": {
                        "article": {"type": "article"},
                        "comment": {"type": "comment"},
                        "person": {"type": "person"},
                        "creator": {"type": "creator"}
                    }
                },
            }
        ]
        + model_types_in_yaml_with_origin,
        metadata_type="RecordMetadata",
    )
    assert issubclass(m.RecordSchema, Schema)
    
    # loaded from yaml in array format
    valid_metadata = {
        "metadata": {
            "article": {"id": 0, "title": "Bob in a Jungle", "tags": ["tag1", "tag2"]},
            "comment": {
                "id": 1,
                "article_id": 1,
                "content": "Comment",
                "author": {"name": "Bob", "age": 123},
            },
        }
    }
    assert m.RecordSchema().load(valid_metadata) == valid_metadata
    assert m2.RecordSchema().load(valid_metadata) == valid_metadata

    # loaded from yaml in dict format
    valid_metadata = {"metadata": {"person": {"id": 0, "name": "Bob", "age": 123}}}
    assert m.RecordSchema().load(valid_metadata) == valid_metadata
    assert m2.RecordSchema().load(valid_metadata) == valid_metadata
    
    valid_metadata = {"metadata": {"creator": {"id": 0, "handles": ["1", "2","3"], "active": True}}}
    assert m.RecordSchema().load(valid_metadata) == valid_metadata
    assert m2.RecordSchema().load(valid_metadata) == valid_metadata
    
    invalid_metadata = {
        "metadata": {
            "person": {
                "id": "1",
                "name": "Bob",
                "age": 123,
            }
        }
    }
    with pytest.raises(ma.exceptions.ValidationError):
        m.RecordSchema().load(invalid_metadata)
    with pytest.raises(ma.exceptions.ValidationError):
        m2.RecordSchema().load(invalid_metadata)    
        
    invalid_metadata = {"metadata": {"creator": {"id": 0, "handles": ["1", "2","3"], "active": "not bool"}}}
    with pytest.raises(ma.exceptions.ValidationError):
        m.RecordSchema().load(invalid_metadata)   
    with pytest.raises(ma.exceptions.ValidationError):
        m2.RecordSchema().load(invalid_metadata)      
        
    invalid_metadata = {
        "metadata": {
            "article": {
                "id": "1",  # should be int
            }
        }
    }
    with pytest.raises(ma.exceptions.ValidationError):
        m.RecordSchema().load(invalid_metadata)     
    with pytest.raises(ma.exceptions.ValidationError):
        m2.RecordSchema().load(invalid_metadata)       
    invalid_metadata = {
        "metadata": {
            "comment": {
                "id": "1",  # should be int
            }
        }
    }
    with pytest.raises(ma.exceptions.ValidationError):
        m.RecordSchema().load(invalid_metadata)           
    with pytest.raises(ma.exceptions.ValidationError):
        m2.RecordSchema().load(invalid_metadata)          