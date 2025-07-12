import copy
import json
import sys
import time

import marshmallow as ma
import pytest
from flask_principal import Identity, Need, UserNeed
from invenio_records_resources.services.records.schema import BaseRecordSchema
from marshmallow.utils import get_value
from marshmallow_utils.fields import SanitizedUnicode

pytest_plugins = ("celery.contrib.pytest",)


class MetadataSchema(ma.Schema):
    title = ma.fields.String(required=True)


class FilesSchema(ma.Schema):
    """Basic files schema class."""

    enabled = ma.fields.Bool(missing=True)
    # allow unsetting
    default_preview = SanitizedUnicode(allow_none=True)

    def get_attribute(self, obj, attr, default):
        """Override how attributes are retrieved when dumping.

        NOTE: We have to access by attribute because although we are loading
              from an external pure dict, but we are dumping from a data-layer
              object whose fields should be accessed by attributes and not
              keys. Access by key runs into FilesManager key access protection
              and raises.
        """
        value = getattr(obj, attr, default)

        if attr == "default_preview" and not value:
            return default

        return value


class TestRecordSchema(BaseRecordSchema):
    """Test RecordSchema."""

    metadata = ma.fields.Nested(MetadataSchema)
    files = ma.fields.Nested(FilesSchema, required=True)

    def get_attribute(self, obj, attr, default):
        """Override how attributes are retrieved when dumping.

        NOTE: We have to access by attribute because although we are loading
              from an external pure dict, but we are dumping from a data-layer
              object whose fields should be accessed by attributes and not
              keys. Access by key runs into FilesManager key access protection
              and raises.
        """
        if attr == "files":
            return getattr(obj, attr, default)
        else:
            return get_value(obj, attr, default)


jsonschema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "metadata": {
            "type": "object",
            "properties": {"title": {"type": "string"}},
        }
    },
}

mapping = {
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

parent_json_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "local://parent-v1.0.0.json",
    "type": "object",
    "properties": {"id": {"type": "string"}},
}


@pytest.fixture(scope="module")
def empty_model():
    from oarepo_model.api import model
    from oarepo_model.customizations import AddClass, AddFileToModule
    from oarepo_model.presets.records_resources import records_resources_presets

    t1 = time.time()

    empty_model = model(
        name="test",
        version="1.0.0",
        presets=[records_resources_presets],
        customizations=[
            AddClass("RecordSchema", TestRecordSchema),
            AddFileToModule(
                "jsonschemas",
                "test-v1.0.0.json",
                json.dumps(jsonschema),
            ),
            # needs https://github.com/inveniosoftware/invenio-search/pull/238/files
            AddFileToModule(
                "mappings",
                "os-v2/test/metadata-v1.0.0.json",
                json.dumps(mapping),
            ),
        ],
    )
    empty_model.register()

    t2 = time.time()
    print(f"Model created in {t2 - t1:.2f} seconds", file=sys.stderr, flush=True)

    return empty_model


@pytest.fixture(scope="module")
def draft_model():
    from oarepo_model.api import model
    from oarepo_model.customizations import AddClass, AddFileToModule
    from oarepo_model.presets.drafts import drafts_records_presets
    from oarepo_model.presets.records_resources import records_presets

    t1 = time.time()
    mapping_with_parent = copy.deepcopy(mapping)
    mapping_with_parent["mappings"]["properties"]["parent"] = {
        "properties": {
            "id": {"type": "keyword"},
        }
    }

    draft_model = model(
        name="draft_test",
        version="1.0.0",
        presets=[records_presets, drafts_records_presets],
        customizations=[
            AddClass("RecordSchema", TestRecordSchema),
            AddFileToModule(
                "jsonschemas",
                "draft_test-v1.0.0.json",
                json.dumps(jsonschema),
            ),
            # needs https://github.com/inveniosoftware/invenio-search/pull/238/files
            # draft metadata mapping
            AddFileToModule(
                "mappings",
                "os-v2/draft_test/draft-metadata-v1.0.0.json",
                json.dumps(mapping_with_parent),
            ),
            # record metadata mapping
            AddFileToModule(
                "mappings",
                "os-v2/draft_test/metadata-v1.0.0.json",
                json.dumps(mapping_with_parent),
            ),
            # add parent JSON schema
            AddFileToModule(
                "jsonschemas",
                "parent-v1.0.0.json",
                json.dumps(
                    {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "$id": "local://parent-v1.0.0.json",
                        "type": "object",
                        "properties": {"id": {"type": "string"}},
                    }
                ),
            ),
        ],
    )
    draft_model.register()

    t2 = time.time()
    print(f"Model created in {t2 - t1:.2f} seconds", file=sys.stderr, flush=True)

    return draft_model


@pytest.fixture(scope="module")
def draft_model_with_files():
    from oarepo_model.api import model
    from oarepo_model.customizations import AddClass, AddFileToModule
    from oarepo_model.presets.drafts import drafts_presets
    from oarepo_model.presets.records_resources import records_resources_presets

    t1 = time.time()
    mapping_with_parent = copy.deepcopy(mapping)
    mapping_with_parent["mappings"]["properties"]["parent"] = {
        "properties": {
            "id": {"type": "keyword"},
        }
    }

    draft_model = model(
        name="draft_with_files",
        version="1.0.0",
        presets=[records_resources_presets, drafts_presets],
        customizations=[
            AddClass("RecordSchema", TestRecordSchema),
            AddFileToModule(
                "jsonschemas",
                "draft_with_files-v1.0.0.json",
                json.dumps(jsonschema),
            ),
            # needs https://github.com/inveniosoftware/invenio-search/pull/238/files
            # draft metadata mapping
            AddFileToModule(
                "mappings",
                "os-v2/draft_with_files/draft-metadata-v1.0.0.json",
                json.dumps(mapping_with_parent),
            ),
            # record metadata mapping
            AddFileToModule(
                "mappings",
                "os-v2/draft_with_files/metadata-v1.0.0.json",
                json.dumps(mapping_with_parent),
            ),
        ],
    )
    draft_model.register()

    t2 = time.time()
    print(f"Model created in {t2 - t1:.2f} seconds", file=sys.stderr, flush=True)

    return draft_model


@pytest.fixture(scope="module")
def app_config(app_config, empty_model, draft_model, draft_model_with_files):
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

    # app_config["SQLALCHEMY_ECHO"] = True

    return app_config


@pytest.fixture(scope="module")
def identity_simple():
    """Simple identity fixture."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(Need(method="system_role", value="any_user"))
    i.provides.add(Need(method="system_role", value="authenticated_user"))
    return i


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    from invenio_app.factory import create_api as _create_api

    return _create_api
