#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Relations whose 'keys' do not list "id" explicitly.

An internal-relation and a self-referencing (lazy) pid-relation are both
*stored* as {"id": ...} no matter what 'keys' says - 'keys' only lists which
fields to embed from the resolved target. Leaving "id" out of it is therefore
legal, and the mapping/json schema/runtime resolution all handle it (they add
"id"/"@v" back unconditionally) - but the relation's marshmallow schema does
not, so the record can no longer be loaded or dumped (see the xfails below).

Fixtures: internal_relation_no_id_key_model / recursive_relation_no_id_key_model
in tests/conftest.py.
"""

from __future__ import annotations

import json

import pytest
from marshmallow import ValidationError

from oarepo_model.utils import resolve_file_content

# LazyMarshmallowSchema.proxied_schema (lazy.py) builds the relation's schema
# from 'keys' alone, with Meta.unknown = RAISE - unlike create_mapping/
# create_json_schema/create_ui_model, which force "id"/"@v" in via
# LazyJSONNamespaceFilePart.extra_fields, and unlike _get_properties, which
# has the same pair as its `fallbacks`. So with "id" not in 'keys' the field
# it is keyed by is neither loadable nor dumpable.
MISSING_ID_FIELD = "the relation's marshmallow schema has no 'id' field unless 'id' is listed in 'keys'"


def test_internal_relation_without_id_key_still_has_id_in_mapping_and_jsonschema(
    app,
    internal_relation_no_id_key_model,
):
    """The mapping and json schema get "id"/"@v" whether 'keys' lists them or not."""
    m = internal_relation_no_id_key_model
    files = m.__files__
    links = m.__symlinks__

    mapping = json.loads(resolve_file_content(files[links["record-mapping-link"]]))
    pp_mapping = mapping["mappings"]["properties"]["metadata"]["properties"]["primary_protein"]
    assert pp_mapping["properties"]["id"] == {"type": "keyword", "ignore_above": 256}
    assert pp_mapping["properties"]["name"] == {"type": "keyword", "ignore_above": 256}
    assert "@v" in pp_mapping["properties"]

    jsonschema = json.loads(resolve_file_content(files[links["record-jsonschema-link"]]))
    pp_schema = jsonschema["properties"]["metadata"]["properties"]["primary_protein"]
    assert pp_schema["properties"]["id"] == {"type": "string"}
    assert pp_schema["properties"]["name"] == {"type": "string"}


@pytest.mark.parametrize(
    ("model_fixture", "relation_name", "expected_keys"),
    [
        ("internal_relation_no_id_key_model", "metadata.primary_protein", ["name"]),
        ("recursive_relation_no_id_key_model", "metadata.direct", ["metadata.title"]),
    ],
)
def test_relation_without_id_key_embeds_only_the_declared_keys(
    app,
    request,
    model_fixture,
    relation_name,
    expected_keys,
):
    """The relation system field dereferences exactly 'keys' - "id" is not added back."""
    model = request.getfixturevalue(model_fixture)
    field = model.Record.relations._fields[relation_name]
    assert field.keys == expected_keys


def test_internal_relation_without_id_key_resolves(app, internal_relation_no_id_key_model):
    """Resolution is keyed off the stored "id", so it works with "id" absent from 'keys'."""
    record = internal_relation_no_id_key_model.Record(
        {
            "metadata": {
                "proteins": [
                    {"id": "p1", "name": "Protein One"},
                    {"id": "p2", "name": "Protein Two"},
                ],
                "primary_protein": {"id": "p1"},
            },
        },
    )

    resolved = getattr(record.relations, "metadata.primary_protein")()
    assert resolved["name"] == "Protein One"


@pytest.mark.xfail(reason=MISSING_ID_FIELD, strict=True, raises=ValidationError)
def test_internal_relation_without_id_key_marshmallow_schema_keeps_id(app, internal_relation_no_id_key_model):
    """The relation's marshmallow schema must still accept and dump the "id" it is keyed by."""
    schema_cls = internal_relation_no_id_key_model.proxies.current_service.schema.schema
    field = schema_cls().fields["metadata"].schema.fields["primary_protein"]

    # raises ValidationError: {'id': ['Unknown field.']}
    assert field.schema.load({"id": "p1"}) == {"id": "p1"}
    # ... and, once that is fixed, the dump drops "id" instead: {'name': 'Protein One'}
    assert field.schema.dump({"id": "p1", "name": "Protein One"}) == {"id": "p1", "name": "Protein One"}


@pytest.mark.xfail(reason=MISSING_ID_FIELD, strict=True, raises=ValidationError)
def test_internal_relation_without_id_key_service_create_and_search(
    app,
    identity_simple,
    internal_relation_no_id_key_model,
    search,
    search_clear,
    location,
    db,
):
    """The full create -> index -> dump cycle with "id" missing from 'keys'."""
    Record = internal_relation_no_id_key_model.Record
    service = internal_relation_no_id_key_model.proxies.current_service

    # raises ValidationError: {'metadata': {'primary_protein': {'id': ['Unknown field.']}}}
    rec = service.create(
        identity_simple,
        {
            "files": {"enabled": False},
            "metadata": {
                "proteins": [
                    {"id": "p1", "name": "Protein One"},
                    {"id": "p2", "name": "Protein Two"},
                ],
                "primary_protein": {"id": "p1"},
            },
        },
    )

    md = rec.data["metadata"]
    assert md["primary_protein"]["id"] == "p1"
    assert md["primary_protein"]["name"] == "Protein One"

    Record.index.refresh()

    hits = service.search(identity_simple, q='metadata.primary_protein.name:"Protein One"', size=25, page=1)
    assert hits.total == 1
    assert next(iter(hits.hits))["id"] == rec.id


@pytest.mark.xfail(reason=MISSING_ID_FIELD, strict=True, raises=ValidationError)
def test_recursive_relation_without_id_key_service_create(
    app,
    identity_simple,
    recursive_relation_no_id_key_model,
    search,
    search_clear,
    location,
    db,
):
    """Same for a self-referencing pid relation, where the "id" is the target record's PID."""
    Record = recursive_relation_no_id_key_model.Record
    service = recursive_relation_no_id_key_model.proxies.current_service

    target_id = service.create(
        identity_simple,
        {"files": {"enabled": False}, "metadata": {"title": "Target record"}},
    ).id
    Record.index.refresh()

    # raises ValidationError: {'metadata': {'direct': {'id': ['Unknown field.']}}}
    rec = service.create(
        identity_simple,
        {
            "files": {"enabled": False},
            "metadata": {"title": "Referencing record", "direct": {"id": target_id}},
        },
    )

    md = rec.data["metadata"]
    assert md["direct"]["id"] == target_id
    assert md["direct"]["metadata"]["title"] == "Target record"
