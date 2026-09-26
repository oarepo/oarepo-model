# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

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

from oarepo_model.customizations import (
    AddFacetGroup,
    AddMetadataExport,
    AddMetadataImport,
    SetDefaultSearchFields,
)
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
        from_json(str(Path(__file__).parent / "data_types_in_json_dict.json")),
        from_json(str(Path(__file__).parent / "data_types_in_json_list.json")),
    ]


@pytest.fixture(scope="session")
def model_types_in_yaml():
    """Model types fixture."""
    # Define the model types used in the tests
    return [
        from_yaml(str(Path(__file__).parent / "data_types_in_yaml_list.yaml")),
        from_yaml(str(Path(__file__).parent / "data_types_in_yaml_dict.yaml")),
    ]


@pytest.fixture(scope="session")
def model_types_in_json_with_origin():
    """Model types fixture."""
    # Define the model types used in the tests
    return [
        from_json(
            "data_types_in_json_dict.json",
            origin=str(Path(__file__).parent / "data_types_in_json_dict.json"),
        ),
        from_json(
            "data_types_in_json_list.json",
            origin=str(Path(__file__).parent / "data_types_in_json_list.json"),
        ),
    ]


@pytest.fixture(scope="session")
def model_types_in_yaml_with_origin():
    """Model types fixture."""
    # Define the model types used in the tests
    return [
        from_yaml(
            "data_types_in_yaml_list.yaml",
            origin=str(Path(__file__).parent / "data_types_in_yaml_list.yaml"),
        ),
        from_yaml(
            "data_types_in_yaml_dict.yaml",
            origin=str(Path(__file__).parent / "data_types_in_yaml_dict.yaml"),
        ),
    ]


#
# Note: models must be created in the top-level conftest.py file
# with fixture scope="session" to ensure they are created only once.
# The reason is that the sqlalchemy engine would otherwise try to map
# the model multiple times, which is not allowed.
#


def _build_model(name, types, presets, customizations=(), **kwargs):
    """Build, register and time a session-scoped test model."""
    from oarepo_model.api import model

    t1 = time.time()
    built = model(
        name=name,
        version=kwargs.pop("version", "1.0.0"),
        presets=presets,
        types=types if isinstance(types, list) else [types],
        metadata_type=kwargs.pop("metadata_type", "Metadata"),
        customizations=list(customizations),
        **kwargs,
    )
    built.register()
    log.info("Model %s created in %.2f seconds", name, time.time() - t1)
    return built


@pytest.fixture(scope="session")
def empty_model(model_types):
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.ui_links import ui_links_preset

    return _build_model(
        "test",
        model_types,
        [records_resources_preset, ui_links_preset],
    )


@pytest.fixture(scope="session")
def synthetic_metadata_model(model_types):
    from oarepo_model.customizations.high_level.set_synthetic_metadata import (
        SetSyntheticMetadata,
    )
    from oarepo_model.presets.records_resources import records_resources_preset

    return _build_model(
        "synthetic_metadata_test",
        model_types,
        [records_resources_preset],
        [
            SetSyntheticMetadata(
                title_upper=lambda d: d["title"].upper(),
            ),
        ],
    )


@pytest.fixture(scope="session")
def csv_imports_model(model_types):
    import csv
    import io
    from typing import Any

    from flask_resources.deserializers.base import DeserializerMixin

    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.ui_links import ui_links_preset

    class CSVRowToMetadataDeserializer(DeserializerMixin):
        """Minimal CSV deserializer for one-record-per-CSV use case.

        Assumptions:
        - First line contains CSV headers that map directly to metadata fields.
        - Only the first data row is used. (Extend for multi-record as needed.)
        - Performs simple type casting: true/false -> bool, integer strings -> int.
        """

        def __init__(self, *, delimiter: str = ",") -> None:
            self.delimiter = delimiter

        def deserialize(self, data: Any) -> dict[str, Any]:
            reader = csv.DictReader(io.StringIO(data.decode("utf-8")), delimiter=self.delimiter)
            row = next(reader, None)
            if row is None:
                return {"metadata": {}, "files": {"enabled": True}}
            metadata = {k: self._cast(v) for k, v in row.items()}
            return {"metadata": metadata, "files": {"enabled": True}}

        @staticmethod
        def _cast(v: str | None) -> Any:
            if v is None:
                return None
            s = v.strip()
            if s == "":
                return None
            low = s.lower()
            if low in ("true", "false"):
                return low == "true"
            # Simple int cast (extend with float/date as needed)
            if low.isdigit() or (low.startswith("-") and low[1:].isdigit()):
                try:
                    return int(low)
                except ValueError:
                    pass
            return s

    return _build_model(
        "csv_imports_test",
        model_types,
        [records_resources_preset, ui_links_preset],
        [
            AddMetadataImport(
                code="csv",
                name=_("CSV"),
                mimetype="text/csv",
                deserializer=CSVRowToMetadataDeserializer(),
                description=_("CSV import"),
                oai_name=("test-namespace", "test-csv"),
            )
        ],
    )


@pytest.fixture(scope="session")
def datacite_exports_model(model_types):
    import json
    from typing import Any

    from flask_resources.serializers import BaseSerializer

    from oarepo_model.presets.drafts import drafts_records_preset
    from oarepo_model.presets.records_resources import records_preset
    from oarepo_model.presets.ui import ui_preset
    from oarepo_model.presets.ui_links import ui_links_preset

    class DataciteSerializer(BaseSerializer):
        """Minimal datacite serializer stub used in tests."""

        def serialize_object(self, _obj) -> dict[str, Any]:
            """Serialize a single object."""
            with (Path(__file__).parent / "data/datacite_export.json").open() as f:
                return json.load(f)["data"]["attributes"]

    return _build_model(
        "datacite_export_test",
        model_types,
        [records_preset, drafts_records_preset, ui_links_preset, ui_preset],
        [
            AddMetadataExport(
                code="datacite",
                name=_("Datacite"),
                mimetype="application/vnd.datacite.datacite+json",
                serializer=DataciteSerializer(),
                display=True,
                oai_metadata_prefix=None,
                oai_schema=None,
                oai_namespace=None,
            )
        ],
        configuration={"ui_blueprint_name": "datacite_export_test_ui"},
    )


@pytest.fixture(scope="session")
def draft_model(model_types):
    from oarepo_model.presets.drafts import drafts_records_preset
    from oarepo_model.presets.records_resources import records_preset
    from oarepo_model.presets.ui_links import ui_links_preset

    return _build_model(
        "draft_test",
        model_types,
        [records_preset, drafts_records_preset, ui_links_preset],
        [SetDefaultSearchFields("title")],
    )


@pytest.fixture(scope="session")
def facet_model(model_types):
    from oarepo_model.presets.drafts import drafts_records_preset
    from oarepo_model.presets.records_resources import records_preset

    return _build_model(
        "facet_test",
        [facet_model_types, record_model_types],
        [records_preset, drafts_records_preset],
        [
            AddFacetGroup("curator", ["metadata.b", "metadata.jej.c", "metadata.vlastni"]),
            AddFacetGroup("default", ["metadata.b", "metadata.jej.c"]),
            AddFacetGroup("owner", ["metadata.jej.c", "metadata.b"]),
        ],
        record_type="Record",
    )


@pytest.fixture(scope="session")
def draft_model_with_files(model_types):
    from oarepo_model.presets.drafts import drafts_preset
    from oarepo_model.presets.records_resources import records_resources_preset

    return _build_model(
        "draft_with_files",
        model_types,
        [records_resources_preset, drafts_preset],
    )


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
            "languages[]": {"type": "keyword"},
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
            "kckckc": {
                "type": "object",
                "properties": {
                    "tttttt[]": {
                        "items": {
                            "type": "object",
                            "properties": {"c": {"type": "keyword"}},
                        },
                    }
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
record_model_types = {"Record": {"properties": {"modifiers": {"type": "keyword"}}}}
relation_model_types = {
    "Metadata": {
        "properties": {
            "direct": {
                "type": "pid-relation",
                "keys": ["id", {"metadata.title": {"type": "keyword"}}],
                "record_cls": "runtime_models_test:Record",
            },
            "array": {
                "type": "array",
                "items": {
                    "type": "pid-relation",
                    "keys": ["id", {"metadata.title": {"type": "keyword"}}],
                    "record_cls": "runtime_models_test:Record",
                },
            },
            "object": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "pid-relation",
                        "keys": ["id", {"metadata.title": {"type": "keyword"}}],
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
                                "keys": ["id", {"metadata.title": {"type": "keyword"}}],
                                "record_cls": "runtime_models_test:Record",
                            },
                        },
                    },
                },
            },
            "triple_array": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "array": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "array": {
                                        "type": "array",
                                        "items": {
                                            "type": "pid-relation",
                                            "keys": ["id", {"metadata.title": {"type": "keyword"}}],
                                            "record_cls": "runtime_models_test:Record",
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
            "multilingual": {
                # test that relations are not broken in multilingual fields
                "type": "multilingual",
            },
            "i18n": {
                # test that relations are not broken in i18n fields
                "type": "i18n",
            },
            "i18ndict": {
                # test that relations are not broken in i18n fields with dict structure
                "type": "i18ndict",
            },
        },
    },
}

recursive_relation_model_types = {
    "Metadata": {
        "properties": {
            "direct": {
                "type": "lazy-pid-relation",
                "keys": ["id", "metadata.title", "metadata.multilingual"],
                "model": "recursive_relation_test",
            },
            "array": {
                "type": "array",
                "items": {
                    "type": "lazy-pid-relation",
                    "keys": ["id", "metadata.title", "metadata.multilingual"],
                    "model": "recursive_relation_test",
                },
            },
            "object": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "lazy-pid-relation",
                        "keys": ["id", "metadata.title", "metadata.multilingual"],
                        "model": "recursive_relation_test",
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
                                "type": "lazy-pid-relation",
                                "keys": ["id", "metadata.title", "metadata.multilingual"],
                                "model": "recursive_relation_test",
                            },
                        },
                    },
                },
            },
            "triple_array": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "array": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "array": {
                                        "type": "array",
                                        "items": {
                                            "type": "lazy-pid-relation",
                                            "keys": ["id", "metadata.title", "metadata.multilingual"],
                                            "model": "recursive_relation_test",
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
            "multilingual": {
                # test that relations are not broken in multilingual fields
                "type": "multilingual",
            },
            "i18n": {
                # test that relations are not broken in i18n fields
                "type": "i18n",
            },
            "i18ndict": {
                # test that relations are not broken in i18n fields with dict structure
                "type": "i18ndict",
            },
            "title": {
                "type": "keyword",
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
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.relations import relations_preset

    return _build_model(
        "relation_test",
        relation_model_types,
        [records_resources_preset, relations_preset],
    )


@pytest.fixture(scope="session")
def recursive_relation_model(empty_model):
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.relations import relations_preset
    from oarepo_model.presets.ui import ui_preset

    return _build_model(
        "recursive_relation_test",
        recursive_relation_model_types,
        [records_resources_preset, relations_preset, ui_preset],
    )


@pytest.fixture(scope="session")
def records_cf_model(model_types):
    from oarepo_model.presets.custom_fields import custom_fields_preset
    from oarepo_model.presets.records_resources import records_resources_preset

    return _build_model(
        "records_cf",
        model_types,
        [records_resources_preset, custom_fields_preset],
    )


geo_model_types = {
    "Metadata": {
        "properties": {
            "title": {"type": "fulltext+keyword"},
            "location": {"type": "geo_point"},
            "shape": {"type": "geo_shape"},
            "shapes": {"type": "array", "items": {"type": "geo_shape"}},
        },
    },
}


@pytest.fixture(scope="session")
def geo_model():
    from oarepo_model.presets.records_resources import records_preset

    return _build_model("geo_test", geo_model_types, [records_preset])


icrs_model_types = {
    "Metadata": {
        "properties": {
            "title": {"type": "fulltext+keyword"},
            "position": {"type": "icrs"},
            "footprint": {"type": "icrs_shape"},
        },
    },
}


@pytest.fixture(scope="session")
def icrs_model():
    from oarepo_model.presets.records_resources import records_preset

    return _build_model("icrs_test", icrs_model_types, [records_preset])


@pytest.fixture(scope="session")
def drafts_cf_model(model_types):
    from oarepo_model.presets.custom_fields import custom_fields_preset
    from oarepo_model.presets.drafts import drafts_preset
    from oarepo_model.presets.records_resources import records_resources_preset

    return _build_model(
        "drafts_cf",
        model_types,
        [records_resources_preset, drafts_preset, custom_fields_preset],
    )


@pytest.fixture(scope="session")
def vocabulary_model(empty_model):
    from oarepo_model.customizations import (
        SetIndexNestedFieldsLimit,
        SetIndexTotalFieldsLimit,
    )
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.relations import relations_preset
    from oarepo_model.presets.ui import ui_preset

    return _build_model(
        "vocabulary_test",
        vocabulary_model_types,
        [records_resources_preset, relations_preset, ui_preset],
        [
            SetIndexTotalFieldsLimit(2000),
            SetIndexNestedFieldsLimit(1000),
        ],
    )


@pytest.fixture(scope="session")
def multilingual_model(empty_model):
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.relations import relations_preset

    return _build_model(
        "multilingual_test",
        multilingual_model_types,
        [records_resources_preset, relations_preset],
    )


@pytest.fixture(scope="session")
def ui_links_model(model_types):
    from oarepo_model.presets.drafts import drafts_records_preset
    from oarepo_model.presets.records_resources import records_preset
    from oarepo_model.presets.ui import ui_preset
    from oarepo_model.presets.ui_links import ui_links_preset

    return _build_model(
        "test_ui_links",
        model_types,
        [records_preset, drafts_records_preset, ui_links_preset, ui_preset],
        configuration={"ui_blueprint_name": "test_ui_links_ui"},
    )


internal_relation_model_types = {
    "Metadata": {
        "properties": {
            "proteins": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "keyword"},
                    },
                },
            },
            "instruments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "keyword"},
                    },
                },
            },
            "primary_protein": {
                "type": "internal-relation",
                "target": "metadata.proteins",
                "keys": ["id", "name"],
            },
        },
    },
}


# Model types for testing internal relations with nested keys (e.g., "provider.name").
# The target's leaf fields carry explicit labels so that a ui model resolved from
# the target can be told apart from ReferenceUIModel's generic fallback (which
# would label them {"und": "name"}).
internal_relation_nested_key_model_types = {
    "Metadata": {
        "properties": {
            "proteins": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "keyword", "label": {"en": "Protein name"}},
                        "provider": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "keyword", "label": {"en": "Provider name"}},
                            },
                        },
                    },
                },
            },
            "primary_protein": {
                "type": "internal-relation",
                "target": "metadata.proteins",
                "keys": ["id", "name", "provider.name"],
            },
        },
    },
}


@pytest.fixture(scope="session")
def internal_relation_model(empty_model):
    from oarepo_model.presets.internal_relations import internal_relations_preset
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.relations import relations_preset
    from oarepo_model.presets.ui import ui_preset

    return _build_model(
        "ir_test",
        internal_relation_model_types,
        [records_resources_preset, relations_preset, internal_relations_preset, ui_preset],
    )


# Model types for testing an internal-relation whose target is an array of a
# *polymorphic* type (e.g. "entities" can hold "person" or "organization"
# variants) - the target's JSON schema is a `{"oneOf": [...]}` node with no
# top-level "properties" of its own (see PolymorphicDataType.create_json_schema),
# so resolving 'keys' like "id"/"name" (present on both variants, via
# "PersonEntity"/"OrganizationEntity") against it must union the "properties"
# of every oneOf branch instead of finding none at all.
internal_relation_polymorphic_target_model_types = {
    "Metadata": {
        "properties": {
            "entities": {
                "type": "array",
                "items": {
                    "type": "polymorphic",
                    "discriminator": "entity_type",
                    "oneof": [
                        {"discriminator": "person", "type": "PersonEntity"},
                        {"discriminator": "organization", "type": "OrganizationEntity"},
                    ],
                },
            },
            "primary_entity": {
                "type": "internal-relation",
                "target": "metadata.entities",
                "keys": ["id", "name"],
            },
        },
    },
    "PersonEntity": {
        "type": "object",
        "properties": {
            "id": {"type": "keyword"},
            "name": {"type": "keyword"},
            "first_name": {"type": "keyword"},
        },
    },
    "OrganizationEntity": {
        "type": "object",
        "properties": {
            "id": {"type": "keyword"},
            "name": {"type": "keyword"},
            "registration_number": {"type": "keyword"},
        },
    },
}


@pytest.fixture(scope="session")
def internal_relation_polymorphic_target_model(empty_model):
    """Model with an internal relation targeting an array of a polymorphic type."""
    from oarepo_model.presets.internal_relations import internal_relations_preset
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.relations import relations_preset
    from oarepo_model.presets.ui import ui_preset

    return _build_model(
        "ir_polymorphic_test",
        internal_relation_polymorphic_target_model_types,
        [records_resources_preset, relations_preset, internal_relations_preset, ui_preset],
    )


@pytest.fixture(scope="session")
def internal_relation_nested_key_model(empty_model):
    """Model with internal relation using nested keys like 'provider.name'."""
    from oarepo_model.presets.internal_relations import internal_relations_preset
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.relations import relations_preset
    from oarepo_model.presets.ui import ui_preset

    return _build_model(
        "irnkd",
        internal_relation_nested_key_model_types,
        [records_resources_preset, relations_preset, internal_relations_preset, ui_preset],
    )


internal_relation_draft_model_types = {
    "Metadata": {
        "properties": {
            "proteins": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "keyword"},
                    },
                },
            },
            "instruments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "keyword"},
                    },
                },
            },
            "primary_protein": {
                "type": "internal-relation",
                "target": "metadata.proteins",
                "keys": ["id", "name"],
            },
        },
    },
}


# Model types for testing array internal relations and validation
internal_relation_array_model_types = {
    "Metadata": {
        "properties": {
            "proteins": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "keyword"},
                    },
                },
            },
            "instruments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "keyword"},
                    },
                },
            },
            "primary_protein": {
                "type": "internal-relation",
                "target": "metadata.proteins",
                "keys": ["id", "name"],
            },
            "used_instruments": {
                "type": "array",
                "items": {
                    "type": "internal-relation",
                    "target": "metadata.instruments",
                    "keys": ["id", "name"],
                },
            },
        },
    },
}


@pytest.fixture(scope="session")
def internal_relation_draft_model(empty_model):
    from oarepo_model.presets.drafts import drafts_preset
    from oarepo_model.presets.internal_relations import internal_relations_preset
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.relations import relations_preset
    from oarepo_model.presets.ui import ui_preset

    return _build_model(
        "ir_draft_test",
        internal_relation_draft_model_types,
        [
            records_resources_preset,
            drafts_preset,
            relations_preset,
            internal_relations_preset,
            ui_preset,
        ],
    )


@pytest.fixture(scope="session")
def internal_relation_array_model(empty_model):
    """Model with an array internal relation (used_instruments) for testing."""
    from oarepo_model.presets.internal_relations import internal_relations_preset
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.relations import relations_preset
    from oarepo_model.presets.ui import ui_preset

    return _build_model(
        "ir_array_test",
        internal_relation_array_model_types,
        [records_resources_preset, relations_preset, internal_relations_preset, ui_preset],
    )


# Model types for testing nested-relation discovery inside an internal
# relation's own target: "producer" is a self-referencing lazy-pid-relation
# (points back at this same model, by name - the same pattern
# recursive_relation_model uses) declared *inside* the "proteins" array items -
# i.e. inside "primary_protein"'s own target schema, not on "primary_protein"
# itself. This exercises InternalRelationDataType's (inherited from
# LazyPIDRelation) _resolve_nested_relation_fields actually discovering and
# registering such a nested relation field (not just plain keyword keys, which
# is all every other internal_relation_* fixture has) - and, because
# "producer" is itself self-referencing, its own create_relations also always
# defers via AddLazyRelation, so resolving "producer" also exercises the
# "a nested customization is itself lazily-resolved" branch (see the matching
# comment in LazyPIDRelation._resolve_nested_relation_fields, lazy_relations.py).
internal_relation_nested_model_types = {
    "Metadata": {
        "properties": {
            "proteins": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "keyword"},
                        "producer": {
                            "type": "lazy-pid-relation",
                            "keys": ["id"],
                            "model": "ir_nested_test",
                        },
                    },
                },
            },
            "instruments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "keyword"},
                    },
                },
            },
            "primary_protein": {
                "type": "internal-relation",
                "target": "metadata.proteins",
                "keys": ["id", "name", "producer"],
            },
        },
    },
}


@pytest.fixture(scope="session")
def internal_relation_nested_model(empty_model):
    """Model whose internal-relation target itself contains a further relation.

    "producer" self-references this same model ("ir_nested_test") by name,
    the same pattern `recursive_relation_model` uses. This is safe to resolve
    lazily (see `internal_relation_nested_model_types` above for why an
    internal-relation nested inside another internal-relation's target would
    *not* be safe here) - PIDRelation's own lazy nested-relation resolution
    only ever needs `current_runtime.models[...]` (populated once a model is
    registered, regardless of when it's read), never `api.current_model` (only
    set for the duration of *this* model's own build, long gone by the time
    `_resolve_nested_relation_fields` actually runs).
    """
    from oarepo_model.presets.internal_relations import internal_relations_preset
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.relations import relations_preset
    from oarepo_model.presets.ui import ui_preset

    return _build_model(
        "ir_nested_test",
        internal_relation_nested_model_types,
        [records_resources_preset, relations_preset, internal_relations_preset, ui_preset],
    )


# Model types for relations whose 'keys' do NOT list "id" explicitly. Both
# relation kinds are still keyed by "id" in the stored data ({"id": "p1"} /
# {"id": <pid>}) - only the list of fields to embed from the target omits it.
internal_relation_no_id_key_model_types = {
    "Metadata": {
        "properties": {
            "proteins": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "keyword"},
                    },
                },
            },
            "primary_protein": {
                "type": "internal-relation",
                "target": "metadata.proteins",
                "keys": ["name"],
            },
        },
    },
}


@pytest.fixture(scope="session")
def internal_relation_no_id_key_model(empty_model):
    """Model with an internal relation whose 'keys' omit "id"."""
    from oarepo_model.presets.internal_relations import internal_relations_preset
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.relations import relations_preset
    from oarepo_model.presets.ui import ui_preset

    return _build_model(
        "ir_no_id_test",
        internal_relation_no_id_key_model_types,
        [records_resources_preset, relations_preset, internal_relations_preset, ui_preset],
    )


recursive_relation_no_id_key_model_types = {
    "Metadata": {
        "properties": {
            "title": {"type": "keyword"},
            "direct": {
                "type": "lazy-pid-relation",
                "keys": ["metadata.title"],
                "model": "recursive_no_id_test",
            },
        },
    },
}


@pytest.fixture(scope="session")
def recursive_relation_no_id_key_model(empty_model):
    """Model with a self-referencing pid relation whose 'keys' omit "id"."""
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.relations import relations_preset
    from oarepo_model.presets.ui import ui_preset

    return _build_model(
        "recursive_no_id_test",
        recursive_relation_no_id_key_model_types,
        [records_resources_preset, relations_preset, ui_preset],
    )


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
            field_cls=SanitizedHTML,
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

    # extra-conservative throttle for GeoDistanceParam/GeoShapeParam's
    # Nominatim geocoding fallback, in case a test exercises it without
    # mocking it out - stay well under the public instance's usage policy
    app_config["NOMINATIM_MIN_DELAY_SECONDS"] = 5

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
    recursive_relation_model,
    vocabulary_model,
    multilingual_model,
    ui_links_model,
    datacite_exports_model,
    synthetic_metadata_model,
    internal_relation_model,
    internal_relation_draft_model,
    internal_relation_array_model,
    internal_relation_nested_model,
    internal_relation_nested_key_model,
    internal_relation_no_id_key_model,
    recursive_relation_no_id_key_model,
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
