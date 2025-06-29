import json

import marshmallow as ma
import pytest
from flask_principal import Identity, Need, UserNeed
from invenio_records_resources.services.records.schema import BaseRecordSchema

pytest_plugins = ("celery.contrib.pytest",)


class MetadataSchema(ma.Schema):
    title = ma.fields.String(required=True)


class TestRecordSchema(BaseRecordSchema):
    """Test RecordSchema."""

    metadata = ma.fields.Nested(MetadataSchema)


@pytest.fixture(scope="module")
def empty_model():
    from oarepo_model.api import model
    from oarepo_model.customizations import AddClass, AddFileToModule
    from oarepo_model.presets.records_resources import records_resources_presets

    empty_model = model(
        name="test",
        version="1.0.0",
        presets=[records_resources_presets],
        customizations=[
            AddClass("RecordSchema", TestRecordSchema),
            AddFileToModule(
                "jsonschemas",
                "test-v1.0.0.json",
                json.dumps(
                    {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "type": "object",
                        "properties": {
                            "metadata": {
                                "type": "object",
                                "properties": {"title": {"type": "string"}},
                            }
                        },
                    }
                ),
            ),
            # needs https://github.com/inveniosoftware/invenio-search/pull/238/files
            AddFileToModule(
                "mappings",
                "os-v2/test/metadata-v1.0.0.json",
                json.dumps(
                    {
                        "mappings": {
                            "properties": {
                                "$schema": {
                                    "type": "keyword",
                                },
                                "created": {"type": "date"},
                                "id": {
                                    "type": "keyword",
                                },
                                "metadata": {
                                    "properties": {
                                        "title": {
                                            "type": "text",
                                            "fields": {
                                                "keyword": {
                                                    "type": "keyword",
                                                    "ignore_above": 256,
                                                }
                                            },
                                        }
                                    }
                                },
                                "pid": {
                                    "properties": {
                                        "obj_type": {
                                            "type": "keyword",
                                        },
                                        "pid_type": {
                                            "type": "keyword",
                                        },
                                        "pk": {"type": "long"},
                                        "status": {
                                            "type": "keyword",
                                        },
                                    }
                                },
                                "updated": {"type": "date"},
                                "uuid": {
                                    "type": "keyword",
                                },
                                "version_id": {"type": "long"},
                            }
                        }
                    }
                ),
            ),
        ],
    )
    empty_model.register()
    return empty_model


@pytest.fixture(scope="module")
def app_config(app_config, empty_model):
    """Override pytest-invenio app_config fixture.

    Needed to set the fields on the custom fields schema.
    """
    app_config["FILES_REST_STORAGE_CLASS_LIST"] = {
        "L": "Local",
    }

    app_config["FILES_REST_DEFAULT_STORAGE_CLASS"] = "L"

    app_config["RECORDS_REFRESOLVER_CLS"] = (
        "invenio_records.resolver.InvenioRefResolver"
    )
    app_config["RECORDS_REFRESOLVER_STORE"] = (
        "invenio_jsonschemas.proxies.current_refresolver_store"
    )

    app_config["THEME_FRONTPAGE"] = False

    app_config["SQLALCHEMY_ENGINE_OPTIONS"] = (
        {  # hack to avoid pool_timeout set in invenio_app_rdm
            "pool_pre_ping": False,
            "pool_recycle": 3600,
        }
    )

    return app_config


@pytest.fixture(scope="module")
def identity_simple():
    """Simple identity fixture."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(Need(method="system_role", value="any_user"))
    i.provides.add(Need(method="system_role", value="authenticated_user"))
    return i
