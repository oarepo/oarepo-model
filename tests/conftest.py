import copy
import json
import sys
import time

import pytest
from flask_principal import Identity, Need, UserNeed

from oarepo_model.presets.rdm import rdm_presets
from oarepo_model.presets.records_resources import records_resources_presets

pytest_plugins = ("celery.contrib.pytest",)


parent_json_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "local://parent-v1.0.0.json",
    "type": "object",
    "properties": {"id": {"type": "string"}},
}

model_types = {
    "Metadata": {
        "properties": {
            "title": {"type": "fulltext+keyword", "required": True},
        }
    }
}



@pytest.fixture(scope="module")
def empty_model():
    from oarepo_model.api import model
    from oarepo_model.presets.records_resources import records_resources_presets

    t1 = time.time()

    empty_model = model(
        name="test",
        version="1.0.0",
        presets=[records_resources_presets],
        types=[model_types],
        metadata_type="Metadata",
        customizations=[],
    )
    empty_model.register()

    t2 = time.time()
    print(f"Empty Model created in {t2 - t1:.2f} seconds", file=sys.stderr, flush=True)

    return empty_model


@pytest.fixture(scope="module")
def draft_model():
    from oarepo_model.api import model
    from oarepo_model.customizations import AddFileToModule
    from oarepo_model.presets.drafts import drafts_records_presets
    from oarepo_model.presets.records_resources import records_presets

    t1 = time.time()

    draft_model = model(
        name="draft_test",
        version="1.0.0",
        presets=[records_presets, drafts_records_presets],
        types=[model_types],
        metadata_type="Metadata",
        customizations=[
            # needs https://github.com/inveniosoftware/invenio-search/pull/238/files
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
    print(f"Draft Model created in {t2 - t1:.2f} seconds", file=sys.stderr, flush=True)

    return draft_model


@pytest.fixture(scope="module")
def draft_model_with_files():
    from oarepo_model.api import model
    from oarepo_model.presets.drafts import drafts_presets
    from oarepo_model.presets.records_resources import records_resources_presets

    t1 = time.time()

    draft_model = model(
        name="draft_with_files",
        version="1.0.0",
        presets=[records_resources_presets, drafts_presets],
        types=[model_types],
        metadata_type="Metadata",
        customizations=[],
    )
    draft_model.register()

    t2 = time.time()
    print(f"Model created in {t2 - t1:.2f} seconds", file=sys.stderr, flush=True)

    return draft_model

@pytest.fixture(scope="module")
def rdm_model():

    from oarepo_model.api import model
    from oarepo_model.customizations import AddFileToModule
    from oarepo_model.presets.drafts import drafts_presets
    from oarepo_model.presets.records_resources import records_presets

    t1 = time.time()

    rdm_model = model(
        name="rdm_test",
        version="1.0.0",
        presets=[records_resources_presets, drafts_presets, rdm_presets],
        types=[model_types],
        metadata_type="Metadata",
        customizations=[
            # needs https://github.com/inveniosoftware/invenio-search/pull/238/files
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
    rdm_model.register()
    t2 = time.time()
    print(f"Draft Model created in {t2 - t1:.2f} seconds", file=sys.stderr, flush=True)

    """
    from oarepo_model.api import model
    from oarepo_model.customizations import AddClass, AddFileToModule
    from oarepo_model.presets.drafts import drafts_presets
    from oarepo_model.presets.records_resources import records_presets

    t1 = time.time()
    mapping_with_parent = copy.deepcopy(mapping)
    mapping_with_parent["mappings"]["properties"]["parent"] = {
        "properties": {
            "id": {"type": "keyword"},
        }
    }

    rdm_model = model(
        name="rdm_test",
        version="1.0.0",
        presets=[records_presets, drafts_presets, rdm_presets],
        customizations=[
            AddClass("RecordSchema", TestRecordSchema),
            AddFileToModule(
                "jsonschemas",
                "rdm_test-v1.0.0.json",
                json.dumps(jsonschema),
            ),
            # needs https://github.com/inveniosoftware/invenio-search/pull/238/files
            # draft metadata mapping
            AddFileToModule(
                "mappings",
                "os-v2/rdm_test/draft-metadata-v1.0.0.json",
                json.dumps(mapping_with_parent),
            ),
            # record metadata mapping
            AddFileToModule(
                "mappings",
                "os-v2/rdm_test/metadata-v1.0.0.json",
                json.dumps(mapping_with_parent),
            ),
        ],
    )
    rdm_model.register()

    t2 = time.time()
    print(f"RDM Model created in {t2 - t1:.2f} seconds", file=sys.stderr, flush=True)
    """

    return rdm_model

@pytest.fixture(scope="module")
#def app_config(app_config, empty_model, draft_model, draft_model_with_files):
def app_config(app_config, rdm_model):
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

    app_config["CELERY_ALWAYS_EAGER"] = True
    app_config["CELERY_TASK_ALWAYS_EAGER"] = True

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
