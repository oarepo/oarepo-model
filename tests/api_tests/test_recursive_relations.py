#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import json

from oarepo_runtime.typing import record_from_result

from oarepo_model.utils import resolve_file_content


def test_recursive_relations(
    app,
    identity_simple,
    recursive_relation_model,
    vocabulary_fixtures,
    search,
    search_clear,
    location,
    db,
    client,
    headers,
):
    Record = recursive_relation_model.Record
    service = recursive_relation_model.proxies.current_service

    # Create the target records (records of the same type as the one
    # referencing them)

    rec1_id = service.create(
        identity_simple,
        {
            "files": {"enabled": False},
            "metadata": {
                "title": "Record 1",
                "multilingual": [{"lang": {"id": "cs"}, "value": "blah"}],
            },
        },
    ).id
    rec2_id = service.create(
        identity_simple,
        {"files": {"enabled": False}, "metadata": {"title": "Record 2"}},
    ).id
    rec3_id = service.create(
        identity_simple,
        {"files": {"enabled": False}, "metadata": {"title": "Record 3"}},
    ).id

    # Refresh to make changes live
    Record.index.refresh()

    relation_rec = service.create(
        identity_simple,
        {
            "files": {
                "enabled": False,
            },
            "metadata": {
                "title": "Record referencing other records",
                "direct": {
                    "id": rec1_id,
                },
                "array": [
                    {"id": rec1_id},
                    {"id": rec2_id},
                ],
                "object": {
                    "a": {"id": rec1_id},
                },
                "double_array": [
                    {"array": [{"id": rec1_id}, {"id": rec2_id}]},
                    {"array": [{"id": rec3_id}]},
                ],
                "triple_array": [
                    {
                        "array": [
                            {"array": [{"id": rec1_id}]},
                            {"array": [{"id": rec2_id}, {"id": rec3_id}]},
                        ]
                    }
                ],
            },
        },
    )

    md = relation_rec.data["metadata"]
    assert md["direct"]["id"] == rec1_id
    assert md["direct"]["metadata"]["title"] == "Record 1"
    # rec1's own "lang" vocabulary relation, nested inside the "multilingual"
    # field that "direct" embeds via 'keys', is discovered lazily (see
    # LazyRelationsField/AddLazyRelation in
    # customizations/high_level/add_pid_relation.py) once this
    # self-referencing model has finished building and registering - so it is
    # registered as this record's own relation too, and gets dereferenced
    # here just like it would be when reading rec1 directly.
    assert md["direct"]["metadata"]["multilingual"] == [
        {"lang": {"id": "cs", "title": {"cs": "Čeština", "en": "Czech"}}, "value": "blah"},
    ]

    assert len(md["array"]) == 2
    assert md["array"][0]["id"] == rec1_id
    assert md["array"][0]["metadata"]["title"] == "Record 1"
    assert md["array"][1]["id"] == rec2_id
    assert md["array"][1]["metadata"]["title"] == "Record 2"

    assert md["object"]["a"]["id"] == rec1_id
    assert md["object"]["a"]["metadata"]["title"] == "Record 1"

    assert len(md["double_array"]) == 2
    assert len(md["double_array"][0]["array"]) == 2
    assert md["double_array"][0]["array"][0]["id"] == rec1_id
    assert md["double_array"][0]["array"][0]["metadata"]["title"] == "Record 1"
    assert md["double_array"][0]["array"][1]["id"] == rec2_id
    assert md["double_array"][0]["array"][1]["metadata"]["title"] == "Record 2"
    assert len(md["double_array"][1]["array"]) == 1
    assert md["double_array"][1]["array"][0]["id"] == rec3_id
    assert md["double_array"][1]["array"][0]["metadata"]["title"] == "Record 3"

    assert len(md["triple_array"]) == 1
    assert len(md["triple_array"][0]["array"]) == 2
    assert len(md["triple_array"][0]["array"][0]["array"]) == 1
    assert md["triple_array"][0]["array"][0]["array"][0]["id"] == rec1_id
    assert md["triple_array"][0]["array"][0]["array"][0]["metadata"]["title"] == "Record 1"
    assert len(md["triple_array"][0]["array"][1]["array"]) == 2
    assert md["triple_array"][0]["array"][1]["array"][0]["id"] == rec2_id
    assert md["triple_array"][0]["array"][1]["array"][0]["metadata"]["title"] == "Record 2"
    assert md["triple_array"][0]["array"][1]["array"][1]["id"] == rec3_id
    assert md["triple_array"][0]["array"][1]["array"][1]["metadata"]["title"] == "Record 3"

    # The "@v" marker above (part of md["direct"] via dereferencing) is a
    # transient, in-memory side effect of dumping/indexing the record (see the
    # comment above) - it must never be persisted to the database. Reload the
    # record's underlying DB row fresh (bypassing SQLAlchemy's in-memory
    # identity map) and confirm the raw stored json field contains no "@v".
    record = record_from_result(relation_rec)
    db.session.expire_all()
    reloaded_model = record.model_cls.query.get(record.id)
    assert "@v" not in json.dumps(reloaded_model.json)

    # Check the UI ("vnd.inveniordm.v1+json") serialization of the same
    # self-referencing relations, via the actual resource/HTTP layer. This
    # exercises PIDRelation.create_ui_marshmallow_schema/LazyUIMarshmallowSchema,
    # which goes through the model's own "RecordUISchema" (looked up on the
    # runtime namespace, not on current_runtime.models's service config).
    #
    # Note: this asserts on the *creation* response - once a record is created
    # and then re-fetched via a separate read, invenio only re-embeds the
    # target's "id" (not the full "keys" data) into the relation, regardless of
    # whether the target model is self-referencing (see the "@v" comment
    # above for the source-level explanation) - so a freshly created response
    # is the only place a fully-resolved relation can be observed.
    res = client.post(
        "/recursive-relation-test",
        headers=headers.ui,
        data=json.dumps(
            {
                "files": {"enabled": False},
                "metadata": {
                    "title": "y",
                    "direct": {"id": rec1_id},
                    "array": [{"id": rec1_id}, {"id": rec2_id}],
                    "object": {"a": {"id": rec1_id}},
                },
            }
        ),
    )
    assert res.status_code == 201

    ui = res.json["ui"]
    assert ui.keys() == {
        "created_date_l10n_short",
        "created_date_l10n_medium",
        "created_date_l10n_long",
        "created_date_l10n_full",
        "updated_date_l10n_short",
        "updated_date_l10n_medium",
        "updated_date_l10n_long",
        "updated_date_l10n_full",
        "direct",
        "array",
        "object",
    }

    # "id" has no UI-specific counterpart on the target's RecordUISchema (it is
    # not part of the UI schema at all) and falls back to a raw passthrough
    # field instead of crashing; "metadata.title" does have a real UI field and
    # resolves to the target's actual (UI-formatted) value.
    assert ui["direct"]["id"] == rec1_id
    assert ui["direct"]["metadata"]["title"] == "Record 1"

    assert len(ui["array"]) == 2
    assert ui["array"][0]["id"] == rec1_id
    assert ui["array"][0]["metadata"]["title"] == "Record 1"
    assert ui["array"][1]["id"] == rec2_id
    assert ui["array"][1]["metadata"]["title"] == "Record 2"

    assert ui["object"]["a"]["id"] == rec1_id
    assert ui["object"]["a"]["metadata"]["title"] == "Record 1"


def test_recursive_relations_mapping_and_jsonschema(app, recursive_relation_model):
    """Check that the generated mapping/json schema for a self-referencing relation is correct.

    It should reflect the real fields of the target model (e.g. "multilingual"
    being a proper nested object), instead of falling back to a plain "keyword".
    """
    files = recursive_relation_model.__files__

    mapping = json.loads(resolve_file_content(files["internal/primary_mapping.json"]))
    metadata_mapping = mapping["mappings"]["properties"]["metadata"]["properties"]

    expected_relation_properties = {
        "id": {"type": "keyword"},
        "metadata": {
            "type": "object",
            "properties": {
                "title": {"type": "keyword", "ignore_above": 256},
                "multilingual": {
                    "type": "object",
                    "dynamic": "strict",
                    "properties": {
                        "lang": {
                            "type": "object",
                            "dynamic": "strict",
                            "properties": {
                                "id": {"type": "keyword", "ignore_above": 256},
                                "title": {"type": "object", "dynamic": "true"},
                                "@v": {"type": "keyword", "ignore_above": 256},
                            },
                        },
                        "value": {"type": "keyword", "ignore_above": 256},
                    },
                },
            },
        },
        "@v": {"type": "keyword", "ignore_above": 256},
    }
    # "direct" is a single relation, "array"'s "items" mapping is the relation object
    # itself (opensearch does not have a separate array type in mappings), and
    # "object.a" is a relation nested inside a plain object - all should resolve
    # to the same, correctly-typed properties.
    assert metadata_mapping["direct"]["properties"] == expected_relation_properties
    assert metadata_mapping["array"]["properties"] == expected_relation_properties
    assert metadata_mapping["object"]["properties"]["a"]["properties"] == expected_relation_properties

    jsonschema = json.loads(resolve_file_content(files["internal/primary_jsonschema.json"]))
    metadata_schema = jsonschema["properties"]["metadata"]["properties"]

    expected_relation_schema_properties = {
        "id": {"type": "string"},
        "metadata": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "multilingual": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "unevaluatedProperties": False,
                        "properties": {
                            "lang": {
                                "type": "object",
                                "unevaluatedProperties": False,
                                "properties": {
                                    "id": {"type": "string"},
                                    "title": {
                                        "type": "object",
                                        "additionalProperties": {"type": "string"},
                                    },
                                    "@v": {"type": "string"},
                                },
                            },
                            "value": {"type": "string"},
                        },
                    },
                },
            },
        },
        "@v": {"type": "string"},
    }
    assert metadata_schema["direct"]["properties"] == expected_relation_schema_properties
    assert metadata_schema["array"]["items"]["properties"] == expected_relation_schema_properties
    assert metadata_schema["object"]["properties"]["a"]["properties"] == expected_relation_schema_properties
