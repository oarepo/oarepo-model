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
from typing import Any

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


def test_recursive_relations_ui_model(app, recursive_relation_model):
    """Check that the generated ui.json model for a self-referencing relation is correct.

    Like create_mapping/create_json_schema above (see LazyMapping/
    LazyJSONSchema), PIDRelation.create_ui_model's 'children' is backed by a
    lazily-resolved mapping (LazyUIModelChildren) for self-referencing
    relations - it should reflect the real fields of the target model (e.g.
    "multilingual" resolving all the way down to its nested vocabulary
    "lang" field), instead of being left empty.
    """
    ui_model = recursive_relation_model.ui_model
    metadata_ui_model = ui_model["children"]["metadata"]["children"]

    def ui(label: str, input_type: str, **extra: Any) -> dict[str, Any]:
        return {"help": {"und": ""}, "label": {"und": label}, "hint": {"und": ""}, "input": input_type, **extra}

    expected_relation_children = {
        # "id" has no counterpart on the target's own ui model at all (it is
        # never synthesized there, unlike mapping/json schema) - falls back
        # to a plain keyword input instead of crashing.
        "id": ui("id", "keyword"),
        "metadata": {
            "input": "object",
            "children": {
                "title": ui("title", "keyword"),
                "multilingual": ui(
                    "multilingual",
                    "multilingual",
                    child=ui(
                        "item",
                        "object",
                        children={
                            "lang": ui(
                                "lang",
                                "vocabulary",
                                children={
                                    "id": ui("id", "keyword"),
                                    "title": ui("title", "i18ndict", children={}),
                                    "@v": ui("@v", "keyword"),
                                },
                            ),
                            "value": ui("value", "keyword"),
                        },
                    ),
                ),
            },
        },
    }

    # "direct" is a single relation, "array"'s "child" is the relation's own
    # ui model wrapped under "child" (see ArrayDataType.create_ui_model), and
    # "object.a" is a relation nested inside a plain object - all should
    # resolve to the same, correctly-typed children.
    assert metadata_ui_model["direct"]["children"] == expected_relation_children
    assert metadata_ui_model["array"]["child"]["children"] == expected_relation_children
    assert metadata_ui_model["object"]["children"]["a"]["children"] == expected_relation_children


def test_recursive_relations_facets(app, recursive_relation_model):
    """Check that no (invalid) facets are generated for a self-referencing relation's 'keys'.

    Unlike test_relation_facets in test_relations.py (see its docstring),
    a self-referencing relation's target model is not resolvable yet at
    facet-generation (build) time - and facet generation, unlike
    create_mapping/create_json_schema/create_relations/create_ui_model, has
    no lazy/deferred variant anywhere in this codebase (facet *names* must
    be known and registered via AddToModule synchronously, at build time -
    see RecordFacetsPreset/MetadataFacetsPreset). PIDRelation.get_facet
    deliberately does not guess at types for a target it can't introspect
    (which could produce an invalid facet, e.g. aggregating on a text field
    with no keyword sub-field) - so, for this case only, no facets are
    generated for the relation's keys at all (see
    test_recursive_relations_facets_warning below for the warning this
    logs).
    """
    facets = recursive_relation_model.facets

    for base in ("metadata.direct", "metadata.array", "metadata.object.a"):
        assert not hasattr(facets, f"{base}.id"), f"unexpected facet for {base}.id"
        assert not hasattr(facets, f"{base}.metadata.title"), f"unexpected facet for {base}.metadata.title"

    # the relation's own top-level facet-less-ness doesn't affect unrelated,
    # non-relation fields on the same (self-referencing) model.
    assert hasattr(facets, "metadata.title")


def test_recursive_relations_facets_warning(caplog):
    """Check that PIDRelation.get_facet logs a clear warning for the self-reference fallback.

    Builds its own throwaway model (rather than reusing the session-scoped
    `recursive_relation_model` fixture) so the model build - and the
    warning it triggers - happens inside this test, where caplog can see
    it; `recursive_relation_model` is built once, lazily, the first time
    any test in the session requests it, so its build-time warnings aren't
    reliably observable from an arbitrary later test.
    """
    from oarepo_model.api import model
    from oarepo_model.presets.records_resources import records_resources_preset
    from oarepo_model.presets.relations import relations_preset

    types = {
        "Metadata": {
            "properties": {
                "direct": {
                    "type": "pid-relation",
                    "keys": ["id", "metadata.title"],
                    "model": "rrf_warning_test",
                },
                "title": {"type": "keyword"},
            },
        },
    }

    with caplog.at_level("WARNING", logger="oarepo_model"):
        m = model(
            name="rrf_warning_test",
            version="1.0.0",
            presets=[records_resources_preset, relations_preset],
            types=[types],
            metadata_type="Metadata",
            customizations=[],
        )
        m.register()

    assert not hasattr(m.facets, "metadata.direct.id")
    warnings = [r for r in caplog.records if "Cannot generate facets for the pid-relation's 'keys'" in r.message]
    assert len(warnings) == 1
    assert "rrf_warning_test" in warnings[0].message
