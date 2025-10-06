#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import ClassVar

import pytest
from flask_principal import Identity, Need, UserNeed
from invenio_access.permissions import system_identity
from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services.custom_fields import TextCF
from invenio_vocabularies.cli import _process_vocab
from invenio_vocabularies.factories import VocabularyConfig, get_vocabulary_config
from invenio_vocabularies.records.models import VocabularyType
from marshmallow_utils.fields import SanitizedHTML
from oarepo_runtime.services.records.mapping import update_all_records_mappings

from oarepo_model.customizations import AddDefaultSearchFields, AddFacetGroup
from oarepo_model.datatypes.registry import from_json, from_yaml

log = logging.getLogger("tests")

pytest_plugins = ("celery.contrib.pytest",)


@pytest.fixture(scope="session")
def model_types():
    """Model types fixture."""
    # Define the model types used in the tests
    return {
        "Metadata": {
            "properties": {
                "title": {"type": "fulltext+keyword", "required": True},
                "some_bool_val": {"type": "boolean"},
                "height": {"type": "int"},
            },
        },
    }


@pytest.fixture(scope="session")
def model_types_in_json():
    """Model types fixture."""
    # Define the model types used in the tests
    return [
        from_json("tests/data_types_in_json_dict.json"),
        from_json("tests/data_types_in_json_list.json"),
    ]


@pytest.fixture(scope="session")
def model_types_in_yaml():
    """Model types fixture."""
    # Define the model types used in the tests
    return [
        from_yaml("tests/data_types_in_yaml_list.yaml"),
        from_yaml("tests/data_types_in_yaml_dict.yaml"),
    ]


@pytest.fixture(scope="session")
def model_types_in_json_with_origin():
    """Model types fixture."""
    # Define the model types used in the tests
    return [
        from_json("data_types_in_json_dict.json", origin="tests/data_types_in_json_dict.json"),
        from_json("data_types_in_json_list.json", origin="tests/data_types_in_json_list.json"),
    ]


@pytest.fixture(scope="session")
def model_types_in_yaml_with_origin():
    """Model types fixture."""
    # Define the model types used in the tests
    return [
        from_yaml("data_types_in_yaml_list.yaml", origin="tests/data_types_in_yaml_list.yaml"),
        from_yaml("data_types_in_yaml_dict.yaml", origin="tests/data_types_in_yaml_dict.yaml"),
    ]


#
# Note: models must be created in the top-level conftest.py file
# with fixture scope="session" to ensure they are created only once.
# The reason is that the sqlalchemy engine would otherwise try to map
# the model multiple times, which is not allowed.
#


@pytest.fixture(scope="session")
def empty_model(model_types):
    from oarepo_model.api import model
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.ui_links import ui_links_preset

    t1 = time.time()

    empty_model = model(
        name="test",
        version="1.0.0",
        presets=[records_resources_preset, ui_links_preset],
        types=[model_types],
        metadata_type="Metadata",
        customizations=[],
    )
    empty_model.register()

    t2 = time.time()
    log.info("Model created in %.2f seconds", t2 - t1)

    return empty_model


@pytest.fixture(scope="session")
def draft_model(model_types):
    from oarepo_model.api import model
    from oarepo_model.presets.drafts import drafts_records_preset
    from oarepo_model.presets.records_resources import records_preset
    from oarepo_model.presets.ui_links import ui_links_preset

    t1 = time.time()

    draft_model = model(
        name="draft_test",
        version="1.0.0",
        presets=[records_preset, drafts_records_preset, ui_links_preset],
        types=[model_types],
        metadata_type="Metadata",
        customizations=[
            AddDefaultSearchFields("title"),
        ],
    )
    draft_model.register()

    t2 = time.time()
    log.info("Model created in %.2f seconds", t2 - t1)

    return draft_model


@pytest.fixture(scope="session")
def facet_model(model_types):
    from oarepo_model.api import model
    from oarepo_model.presets.drafts import drafts_records_preset
    from oarepo_model.presets.records_resources import records_preset

    t1 = time.time()

    facet_model = model(
        name="facet_test",
        version="1.0.0",
        presets=[records_preset, drafts_records_preset],
        types=[facet_model_types],
        metadata_type="Metadata",
        customizations=[
            AddFacetGroup("curator", ["b", "jazyk", "vlastni"]),
            AddFacetGroup("default", ["b", "jazyk"]),
            AddFacetGroup("owner", ["jazyk", "b"]),
        ],
    )

    facet_model.register()

    t2 = time.time()
    log.info("Model created in %.2f seconds", t2 - t1)

    return facet_model


@pytest.fixture(scope="session")
def draft_model_with_files(model_types):
    from oarepo_model.api import model
    from oarepo_model.presets.drafts import drafts_preset
    from oarepo_model.presets.records_resources import records_resources_preset

    t1 = time.time()

    draft_model = model(
        name="draft_with_files",
        version="1.0.0",
        presets=[records_resources_preset, drafts_preset],
        types=[model_types],
        metadata_type="Metadata",
        customizations=[],
    )
    draft_model.register()

    t2 = time.time()
    log.info("Model created in %.2f seconds", t2 - t1)

    return draft_model


facet_model_types = {
    "Metadata": {
        "properties": {
            "jej": {
                "type": "nested",
                "properties": {
                    "c": {
                        "type": "keyword",
                    }
                },
            },
            "multi": {"type": "multilingual"},
            "jazyk": {"type": "i18n"},
            "b": {
                "type": "fulltext+keyword",
            },
            "c": {"type": "fulltext"},
            "vlastni": {
                "type": "keyword",
                "facet-def": {
                    "facet": "oarepo_runtime.services.facets.date.DateFacet",
                    "field": "vlastni.cesta",
                    "label": "jeeej",
                },
            },
            "date": {"type": "date"},
            "time": {"type": "time"},
            "edtf": {"type": "edtf"},
            "edtf-time": {
                "type": "edtf-time",
            },
            "edtf-interval": {
                "type": "edtf-interval",
            },
            "datetime": {
                "type": "datetime",
            },
            "d": {"type": "keyword", "searchable": False},
            "b_nes": {
                "type": "nested",
                "properties": {
                    "c": {
                        "type": "keyword",
                    },
                    "f": {
                        "type": "object",
                        "properties": {"g": {"type": "keyword"}},
                    },
                },
            },
            "b_obj": {
                "type": "object",
                "properties": {
                    "c": {
                        "type": "keyword",
                    },
                    "d": {"type": "fulltext+keyword"},
                    "f": {
                        "type": "nested",
                        "properties": {"g": {"type": "keyword"}},
                    },
                },
            },
            "arr": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "a": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {"c": {"type": "keyword"}},
                            },
                        }
                    },
                },
            },
            "arrnes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "a": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {"c": {"type": "keyword"}},
                            },
                        }
                    },
                },
            },
            "obyc_array": {
                "type": "array",
                "items": {"type": "keyword"},
            },
            "language": {
                "type": "vocabulary",
                "vocabulary-type": "languages",
            },
            "affiliation": {
                "type": "vocabulary",
                "vocabulary-type": "affiliations",
            },
        }
    }
}
relation_model_types = {
    "Metadata": {
        "properties": {
            "direct": {
                "type": "pid-relation",
                "keys": ["id", "metadata.title"],
                "record_cls": "runtime_models_test:Record",
            },
            "array": {
                "type": "array",
                "items": {
                    "type": "pid-relation",
                    "keys": ["id", "metadata.title"],
                    "record_cls": "runtime_models_test:Record",
                },
            },
            "object": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "pid-relation",
                        "keys": ["id", "metadata.title"],
                        "record_cls": "runtime_models_test:Record",
                    },
                },
            },
            "double_array": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "array": {
                            "type": "array",
                            "items": {
                                "type": "pid-relation",
                                "keys": ["id", "metadata.title"],
                                "record_cls": "runtime_models_test:Record",
                            },
                        },
                    },
                },
            },
        },
    },
}

vocabulary_model_types = {
    "Metadata": {
        "properties": {
            "language": {
                "type": "vocabulary",
                "vocabulary-type": "languages",
            },
            "affiliation": {
                "type": "vocabulary",
                "vocabulary-type": "affiliations",
            },
            "funder": {
                "type": "vocabulary",
                "vocabulary-type": "funders",
            },
            "award": {
                "type": "vocabulary",
                "vocabulary-type": "awards",
            },
            "subject": {
                "type": "vocabulary",
                "vocabulary-type": "subjects",
            },
        },
    },
}

multilingual_model_types = {
    "Metadata": {
        "properties": {
            "abstract": {
                "type": "i18n",
                "multilingual": {"lang_name": "jazyk", "value_name": "hodnotka"},
            },
            "title": {
                "type": "i18n",
            },
            "rights": {
                "type": "multilingual",
            },
        }
    }
}


@pytest.fixture(scope="session")
def relation_model(empty_model):
    from oarepo_model.api import model
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.relations import relations_preset

    t1 = time.time()

    relation_model = model(
        name="relation_test",
        version="1.0.0",
        presets=[records_resources_preset, relations_preset],
        types=[relation_model_types],
        metadata_type="Metadata",
        customizations=[],
    )
    relation_model.register()

    t2 = time.time()
    log.info("Model created in %.2f seconds", t2 - t1)

    return relation_model


@pytest.fixture(scope="session")
def records_cf_model(model_types):
    from oarepo_model.api import model
    from oarepo_model.presets.custom_fields import custom_fields_preset
    from oarepo_model.presets.records_resources import records_resources_preset

    m = model(
        name="records_cf",
        version="1.0.0",
        presets=[records_resources_preset, custom_fields_preset],
        types=[model_types],
        metadata_type="Metadata",
        customizations=[],
    )
    m.register()

    return m


@pytest.fixture(scope="session")
def drafts_cf_model(model_types):
    from oarepo_model.api import model
    from oarepo_model.presets.custom_fields import custom_fields_preset
    from oarepo_model.presets.drafts import drafts_preset
    from oarepo_model.presets.records_resources import records_resources_preset

    m = model(
        name="drafts_cf",
        version="1.0.0",
        presets=[records_resources_preset, drafts_preset, custom_fields_preset],
        types=[model_types],
        metadata_type="Metadata",
        customizations=[],
    )
    m.register()

    return m


@pytest.fixture(scope="session")
def vocabulary_model(empty_model):
    from oarepo_model.api import model
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.relations import relations_preset
    from oarepo_model.presets.ui import ui_preset

    t1 = time.time()

    vocabulary_model = model(
        name="vocabulary_test",
        version="1.0.0",
        presets=[records_resources_preset, relations_preset, ui_preset],
        types=[vocabulary_model_types],
        metadata_type="Metadata",
        customizations=[],
    )
    vocabulary_model.register()

    t2 = time.time()
    log.info("Model created in %.2f seconds", t2 - t1)

    return vocabulary_model


@pytest.fixture(scope="session")
def multilingual_model(empty_model):
    from oarepo_model.api import model
    from oarepo_model.presets.records_resources import records_resources_preset

    t1 = time.time()

    multilingual_model = model(
        name="multilingual_test",
        version="1.0.0",
        presets=[records_resources_preset],
        types=[multilingual_model_types],
        metadata_type="Metadata",
        customizations=[],
    )
    multilingual_model.register()

    t2 = time.time()
    log.info("Model created in %.2f seconds", t2 - t1)

    return multilingual_model


@pytest.fixture(scope="session")
def ui_links_model(model_types):
    from oarepo_model.api import model
    from oarepo_model.presets.drafts import drafts_records_preset
    from oarepo_model.presets.records_resources import records_preset
    from oarepo_model.presets.ui import ui_preset
    from oarepo_model.presets.ui_links import ui_links_preset

    t1 = time.time()

    ui_links_model = model(
        name="test_ui_links",
        version="1.0.0",
        presets=[
            records_preset,
            drafts_records_preset,
            ui_links_preset,
            ui_preset,
        ],
        types=[model_types],
        metadata_type="Metadata",
        customizations=[],
        configuration={"ui_blueprint_name": "test_ui_links_ui"},
    )
    ui_links_model.register()

    t2 = time.time()
    log.info("Model created in %.2f seconds", t2 - t1)

    return ui_links_model


@pytest.fixture(scope="module")
def app_config(
    app_config,
):
    """Override pytest-invenio app_config fixture.

    Needed to set the fields on the custom fields schema.
    """
    app_config["FILES_REST_STORAGE_CLASS_LIST"] = {
        "L": "Local",
    }

    app_config["FILES_REST_DEFAULT_STORAGE_CLASS"] = "L"

    app_config["RECORDS_REFRESOLVER_CLS"] = "invenio_records.resolver.InvenioRefResolver"
    app_config["RECORDS_REFRESOLVER_STORE"] = "invenio_jsonschemas.proxies.current_refresolver_store"

    app_config["THEME_FRONTPAGE"] = False

    app_config["SQLALCHEMY_ENGINE_OPTIONS"] = {  # avoid pool_timeout set in invenio_app_rdm
        "pool_pre_ping": False,
        "pool_recycle": 3600,
    }

    app_config["RDM_NAMESPACES"] = {
        "cern": "https://greybook.cern.ch/",
    }

    app_config["RECORDS_CF_CUSTOM_FIELDS"] = {
        TextCF(  # a text input field that will allow HTML tags
            name="cern:experiment",
            field_cls=SanitizedHTML,  # type: ignore[assignment]
        ),
    }

    app_config["DRAFTS_CF_CUSTOM_FIELDS"] = app_config["RECORDS_CF_CUSTOM_FIELDS"]

    app_config["RECORDS_CF_CUSTOM_FIELDS_UI"] = [
        {
            "section": _("CERN Experiment"),
            "fields": [
                {
                    "field": "cern:experiment",
                    "ui_widget": "RichInput",
                    "props": {
                        "label": "Experiment description",
                        "placeholder": "This experiment aims to...",
                        "icon": "pencil",
                        "description": ("You should fill this field with the experiment description.",),
                    },
                },
            ],
        },
    ]

    app_config["DRAFTS_CF_CUSTOM_FIELDS_UI"] = app_config["RECORDS_CF_CUSTOM_FIELDS_UI"]

    # disable CSRF protection for tests
    app_config["REST_CSRF_ENABLED"] = False

    app_config["RDM_PERSISTENT_IDENTIFIERS"] = {}

    app_config["RDM_OPTIONAL_DOI_VALIDATOR"] = lambda _draft, _previous_published, **_kwargs: True

    app_config["DATACITE_TEST_MODE"] = True
    app_config["RDM_RECORDS_ALLOW_RESTRICTION_AFTER_GRACE_PERIOD"] = True

    # for RDM links
    app_config["IIIF_FORMATS"] = ["jpg", "png"]
    app_config["APP_RDM_RECORD_THUMBNAIL_SIZES"] = [500]
    app_config["RDM_ARCHIVE_DOWNLOAD_ENABLED"] = True

    return app_config


@pytest.fixture(scope="module")
def identity_simple():
    """Create simple identity fixture."""
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


@pytest.fixture(scope="module")
def extra_entry_points(
    empty_model,
    draft_model,
    draft_model_with_files,
    records_cf_model,
    facet_model,
    drafts_cf_model,
    relation_model,
    vocabulary_model,
    multilingual_model,
    ui_links_model,
):
    return {
        "invenio_base.blueprints": [
            "invenio_app_rdm_records = tests.mock_module:create_invenio_app_rdm_records_blueprint",
            "iiif = tests.mock_module:create_invenio_app_rdm_iiif_blueprint",
            "rdm_test_links = tests.mock_module:create_invenio_app_rdm_access_links_blueprint",
            "rdm_test_grants = tests.mock_module:create_invenio_app_rdm_access_grants_blueprint",
            "rdm_test_users = tests.mock_module:create_invenio_app_rdm_user_access_blueprint",
            "rdm_test_groups = tests.mock_module:create_invenio_app_rdm_group_access_blueprint",
        ],
    }


@pytest.fixture
def vocabulary_fixtures(app, db, search_clear, search):
    """Import vocabulary fixtures."""
    VocabularyType.create(id="languages", pid_type="lng")
    db.session.commit()

    for vocabulary in (
        "languages",
        "subjects",
        "affiliations",
        "funders",
        "awards",
    ):
        settings = Path(__file__).parent / "vocabulary_data/settings.yaml"
        filepath = Path(__file__).parent / f"vocabulary_data/{vocabulary}.yaml"
        vc = get_vocabulary_config(vocabulary)
        if vc.vocabulary_name:
            config = vc.get_config(settings, origin=filepath)
        else:

            class VC(VocabularyConfig):
                """Names Vocabulary Config."""

                config: ClassVar[dict] = {
                    "readers": [
                        {
                            "type": "yaml",
                            "args": {
                                "regex": "\\.yaml$",
                            },
                        },
                    ],
                    "writers": [
                        {
                            "type": "service",
                            "args": {
                                "service_or_name": "vocabularies",
                                "identity": system_identity,
                            },
                        },
                    ],
                }
                vocabulary_name = vocabulary

            config = VC().get_config(settings, origin=filepath)

        _success, errored, filtered = _process_vocab(config)
        assert errored == 0
        assert filtered == 0


@pytest.fixture(scope="module")
def search(search):
    """Search fixture."""
    update_all_records_mappings()
    return search
