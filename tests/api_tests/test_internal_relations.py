# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Tests for InternalRelationDataType (datatypes/internal_relations.py).

Exercises the lazily-resolved mapping/json schema/marshmallow schema/ui model,
the relation field being registered on `record.relations`, and actually
resolving a relation at runtime via the `internal_relations` lookup-table
system field added by `presets.internal_relations.internal_relations_preset`
(`InternalRelationsLookupPreset` for the Record class,
`InternalRelationsDraftLookupPreset` for the Draft class - see the
`internal_relation_model`/`internal_relation_draft_model` fixtures in
conftest.py).
"""

from __future__ import annotations

import json

import pytest

from oarepo_model.utils import resolve_file_content


def test_internal_relation_mapping_and_jsonschema(app, internal_relation_model):
    """The lazily-resolved mapping/json schema should reflect the target's real fields."""
    m = internal_relation_model
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


def test_internal_relation_polymorphic_target_mapping_and_jsonschema(app, internal_relation_polymorphic_target_model):
    """The relation should resolve 'keys' even when its target is an array of a polymorphic type.

    Regression test: `walk_type_tree_path` used to give up as soon as it hit a
    node with no "properties" key, which is exactly the shape of a polymorphic
    field's JSON schema (`{"oneOf": [...]}` - see
    PolymorphicDataType.create_json_schema). "id"/"name" (declared on both the
    "person" and "organization" variants) must resolve by unioning the
    "properties" of every oneOf branch instead of raising a KeyError.
    """
    m = internal_relation_polymorphic_target_model
    files = m.__files__
    links = m.__symlinks__

    mapping = json.loads(resolve_file_content(files[links["record-mapping-link"]]))
    pe_mapping = mapping["mappings"]["properties"]["metadata"]["properties"]["primary_entity"]
    assert pe_mapping["properties"]["id"] == {"type": "keyword", "ignore_above": 256}
    assert pe_mapping["properties"]["name"] == {"type": "keyword", "ignore_above": 256}

    jsonschema = json.loads(resolve_file_content(files[links["record-jsonschema-link"]]))
    pe_schema = jsonschema["properties"]["metadata"]["properties"]["primary_entity"]
    assert pe_schema["properties"]["id"] == {"type": "string"}
    assert pe_schema["properties"]["name"] == {"type": "string"}


def test_internal_relation_polymorphic_target_resolve(app, internal_relation_polymorphic_target_model):
    """The relation should resolve at runtime regardless of which polymorphic variant it points to."""
    record = internal_relation_polymorphic_target_model.Record(
        {
            "metadata": {
                "entities": [
                    {"entity_type": "person", "id": "e1", "name": "Alice", "first_name": "Alice"},
                    {
                        "entity_type": "organization",
                        "id": "e2",
                        "name": "Acme Corp",
                        "registration_number": "123",
                    },
                ],
                "primary_entity": {"id": "e2"},
            },
        },
    )

    resolved = getattr(record.relations, "metadata.primary_entity")()
    assert resolved["name"] == "Acme Corp"


def test_internal_relation_polymorphic_target_service_and_ui(
    app,
    internal_relation_polymorphic_target_model,
    search,
    search_clear,
    location,
    db,
    client,
    headers,
):
    """Records with a relation into a polymorphic array load, dump and UI-serialize (issue #152).

    The relation's keys are looked up in the marshmallow (and UI) schema of the target
    path, which for a polymorphic field is the merge of all its variants.
    """
    res = client.post(
        "/ir-polymorphic-test",
        headers=headers.ui,
        data=json.dumps(
            {
                "files": {"enabled": False},
                "metadata": {
                    "entities": [
                        {"entity_type": "person", "id": "e1", "name": "Alice", "first_name": "Alice"},
                        {"entity_type": "organization", "id": "e2", "name": "Acme Corp", "registration_number": "1"},
                    ],
                    "primary_entity": {"id": "e2"},
                },
            },
        ),
    )
    assert res.status_code == 201, res.json
    assert res.json["metadata"]["primary_entity"] == {"id": "e2", "name": "Acme Corp"}
    assert res.json["ui"]["primary_entity"]["name"] == "Acme Corp"


def test_internal_relation_marshmallow_schema(app, internal_relation_model):
    """LazyInternalMarshmallowSchema should resolve 'keys' against the target's real fields."""
    schema_cls = internal_relation_model.proxies.current_service.schema.schema
    field = schema_cls().fields["metadata"].schema.fields["primary_protein"]

    # LazyProxiedMarshmallowSchema (see relations.py) only builds/exposes its
    # real fields lazily on load()/dump() - .fields itself stays empty by
    # design (mirrors LazyMarshmallowSchema's own behaviour for pid-relation).
    dumped = field.schema.dump({"id": "p1", "name": "Protein One", "extra": "dropped"})
    assert dumped == {"id": "p1", "name": "Protein One"}

    # keys are copied from the target on save - load keeps only "id", without validating the rest
    assert field.schema.load({"id": "p1", "name": 1, "extra": "dropped"}) == {"id": "p1"}


def test_internal_relation_ui_model(app, internal_relation_model):
    """LazyInternalUIModelChildren should resolve 'keys' against the target's real ui model."""
    ui_model = internal_relation_model.ui_model
    pp_ui = ui_model["children"]["metadata"]["children"]["primary_protein"]
    pp_ui_children = dict(pp_ui["children"])

    assert pp_ui_children["id"]["input"] == "keyword"
    assert pp_ui_children["name"]["input"] == "keyword"


def test_internal_relation_field_registered(app, internal_relation_model):
    """The InternalRelation system field should be registered under record.relations."""
    from oarepo_runtime.records.systemfields.relations import InternalRelation

    field = internal_relation_model.Record.relations._fields["metadata.primary_protein"]
    assert isinstance(field, InternalRelation)
    assert field.target_path == "metadata.proteins"


def test_internal_relation_resolve(app, internal_relation_model):
    """The relation should resolve against the record's own internal_relations lookup table."""
    record = internal_relation_model.Record(
        {
            "metadata": {
                "proteins": [
                    {"id": "p1", "name": "Protein One"},
                    {"id": "p2", "name": "Protein Two"},
                ],
                "instruments": [{"id": "i1", "name": "Instrument One"}],
                "primary_protein": {"id": "p1"},
            },
        },
    )

    resolved = getattr(record.relations, "metadata.primary_protein")()
    assert resolved["name"] == "Protein One"


def test_internal_relation_no_draft_class_without_drafts_preset(internal_relation_model):
    """InternalRelationsDraftLookupPreset's only_if=("Draft",) should skip itself gracefully.

    internal_relation_model does not include drafts_preset, so there is no
    "Draft" class at all for the preset to modify - it must not error out
    (see filter_only_if in api.py), and the model must simply have no Draft.
    """
    assert not hasattr(internal_relation_model, "Draft")


def test_internal_relation_draft_field_registered(app, internal_relation_draft_model):
    """The internal_relations lookup-table system field should also be on the Draft class."""
    from oarepo_runtime.records.systemfields.relations import InternalRelations

    assert isinstance(internal_relation_draft_model.Draft.internal_relations, InternalRelations)


def test_internal_relation_resolve_on_draft(app, internal_relation_draft_model):
    """The relation should resolve on a Draft instance too, not just a published Record."""
    draft = internal_relation_draft_model.Draft(
        {
            "metadata": {
                "proteins": [
                    {"id": "p1", "name": "Protein One"},
                    {"id": "p2", "name": "Protein Two"},
                ],
                "instruments": [{"id": "i1", "name": "Instrument One"}],
                "primary_protein": {"id": "p1"},
            },
        },
    )

    resolved = getattr(draft.relations, "metadata.primary_protein")()
    assert resolved["name"] == "Protein One"


def test_internal_relation_service_create_and_search(
    app,
    identity_simple,
    internal_relation_model,
    search,
    search_clear,
    location,
    db,
):
    """An internal relation should survive the full service create/index/dump cycle.

    `test_internal_relation_resolve` only exercises `.resolve()`/`()` against
    an in-memory `Record()` - it never goes through `RelationDumperExt`/the
    real create -> index -> dump pipeline. This builds a record via the
    actual service (mirroring
    test_recursive_relations.py::test_recursive_relations and
    test_relations.py::test_relations, the "normal"/"recursive" counterparts
    of this same end-to-end check), confirms the dereferenced
    'primary_protein.name' is present on the *create* response, and then -
    the part none of the in-memory tests can show - confirms it was actually
    dumped into the search index by querying OpenSearch for it directly.
    """
    Record = internal_relation_model.Record
    service = internal_relation_model.proxies.current_service

    rec = service.create(
        identity_simple,
        {
            "files": {"enabled": False},
            "metadata": {
                "proteins": [
                    {"id": "p1", "name": "Protein One"},
                    {"id": "p2", "name": "Protein Two"},
                ],
                "instruments": [{"id": "i1", "name": "Instrument One"}],
                "primary_protein": {"id": "p1"},
            },
        },
    )

    md = rec.data["metadata"]
    assert md["primary_protein"]["id"] == "p1"
    assert md["primary_protein"]["name"] == "Protein One"

    # Refresh to make changes live
    Record.index.refresh()

    # The relation's embedded 'name' (not just the raw 'id') must be a real,
    # queryable field in the index - not merely present in the create
    # response - i.e. RelationDumperExt actually dumped the dereferenced
    # value rather than the raw {"id": "p1"} into the indexed document.
    hits = service.search(identity_simple, q='metadata.primary_protein.name:"Protein One"', size=25, page=1)
    assert hits.total == 1, (
        f"Expected 1 hit for 'Protein One', got {hits.total}. "
        "This test exposes whether internal relations are dumped to OpenSearch correctly."
    )
    assert next(iter(hits.hits))["id"] == rec.id

    # A query for the *other* protein's name (present elsewhere in the same
    # record, in "proteins", but not the one "primary_protein" points at)
    # must not match - confirming the index reflects the resolved relation,
    # not just any "name" appearing anywhere in the record.
    no_hits = service.search(identity_simple, q='metadata.primary_protein.name:"Protein Two"', size=25, page=1)
    assert no_hits.total == 0


def test_internal_relation_array_service_create_and_search(
    app,
    identity_simple,
    internal_relation_array_model,
    search,
    search_clear,
    location,
    db,
):
    """Array internal relations should also survive the full service create/index/dump cycle.

    Tests the array case (used_instruments) in addition to the scalar case
    (primary_protein). This creates a record with multiple instruments and an
    array internal relation referencing them, then confirms all dereferenced
    instrument names are queryable in OpenSearch.
    """
    Record = internal_relation_array_model.Record
    service = internal_relation_array_model.proxies.current_service

    rec = service.create(
        identity_simple,
        {
            "files": {"enabled": False},
            "metadata": {
                "proteins": [
                    {"id": "p1", "name": "Protein One"},
                ],
                "instruments": [
                    {"id": "i1", "name": "Spectrometer A"},
                    {"id": "i2", "name": "Microscope B"},
                    {"id": "i3", "name": "Centrifuge C"},
                ],
                "primary_protein": {"id": "p1"},
                "used_instruments": [{"id": "i1"}, {"id": "i3"}],
            },
        },
    )

    md = rec.data["metadata"]
    # Scalar relation
    assert md["primary_protein"]["id"] == "p1"
    assert md["primary_protein"]["name"] == "Protein One"
    # Array relation - verify the create response has dereferenced data
    assert len(md["used_instruments"]) == 2
    assert md["used_instruments"][0]["id"] == "i1"
    assert md["used_instruments"][0]["name"] == "Spectrometer A"
    assert md["used_instruments"][1]["id"] == "i3"
    assert md["used_instruments"][1]["name"] == "Centrifuge C"

    # Refresh to make changes live
    Record.index.refresh()

    # Query for each instrument name that IS in the array relation
    # Note: This may fail if array internal relations aren't dumped correctly
    for instrument_name in ["Spectrometer A", "Centrifuge C"]:
        hits = service.search(identity_simple, q=f'metadata.used_instruments.name:"{instrument_name}"', size=25, page=1)
        assert hits.total == 1, (
            f"Expected 1 hit for {instrument_name}, got {hits.total}. "
            "This test exposes whether array internal relations are dumped correctly."
        )
        assert next(iter(hits.hits))["id"] == rec.id

    # Query for an instrument name that is in the record but NOT in the relation
    no_hits = service.search(identity_simple, q='metadata.used_instruments.name:"Microscope B"', size=25, page=1)
    assert no_hits.total == 0


def test_internal_relation_validate_nonexistent_id(
    app,
    identity_simple,
    internal_relation_model,
    search,
    search_clear,
    location,
    db,
):
    """Internal relations should validate that referenced ids actually exist.

    Verifies that validation raises InvalidRelationValue when referencing an
    id that doesn't exist at the field's target_path.
    """
    from invenio_records.systemfields.relations.errors import InvalidRelationValue

    service = internal_relation_model.proxies.current_service

    # First, create a valid record to use as a base
    valid_rec = service.create(
        identity_simple,
        {
            "files": {"enabled": False},
            "metadata": {
                "proteins": [{"id": "p1", "name": "Protein One"}],
                "instruments": [{"id": "i1", "name": "Instrument One"}],
                "primary_protein": {"id": "p1"},
            },
        },
    )

    # Try to update with a non-existent protein id - should fail validation
    with pytest.raises(InvalidRelationValue) as exc_info:
        service.update(
            identity_simple,
            valid_rec.id,
            {
                "files": {"enabled": False},
                "metadata": {
                    "proteins": [{"id": "p1", "name": "Protein One"}],
                    "instruments": [{"id": "i1", "name": "Instrument One"}],
                    "primary_protein": {"id": "nonexistent"},  # This id doesn't exist
                },
            },
        )

    # The error message should mention the invalid id
    assert "nonexistent" in str(exc_info.value)


def test_internal_relation_add_and_reference_same_request(
    app,
    identity_simple,
    internal_relation_model,
    search,
    search_clear,
    location,
    db,
):
    """Can add a new item and reference it in the same service.create() call.

    Tests that adding a new protein and referencing it as primary_protein in
    the same request works correctly. The lookup table should be built after
    all data is in place, so newly added items should be resolvable.
    """
    Record = internal_relation_model.Record
    service = internal_relation_model.proxies.current_service

    # Create a record with a NEW protein and reference it immediately
    rec = service.create(
        identity_simple,
        {
            "files": {"enabled": False},
            "metadata": {
                "proteins": [
                    {"id": "p-new", "name": "Brand New Protein"},
                    {"id": "p-existing", "name": "Existing Protein"},
                ],
                "instruments": [{"id": "i1", "name": "Instrument One"}],
                "primary_protein": {"id": "p-new"},  # Reference the newly added protein
            },
        },
    )

    md = rec.data["metadata"]
    # The newly added protein should be resolvable in the create response
    assert md["primary_protein"]["id"] == "p-new"
    assert md["primary_protein"]["name"] == "Brand New Protein"

    # Refresh and verify it was dumped correctly
    # Note: This assertion may fail if internal relations aren't dumped correctly
    Record.index.refresh()
    hits = service.search(identity_simple, q='metadata.primary_protein.name:"Brand New Protein"', size=25, page=1)
    assert hits.total == 1, (
        f"Expected 1 hit for 'Brand New Protein', got {hits.total}. "
        "This test exposes whether internal relations are dumped to OpenSearch correctly."
    )
    assert next(iter(hits.hits))["id"] == rec.id


def test_internal_relation_nested_relation_field_registered(app, internal_relation_nested_model):
    """A relation declared inside an internal-relation's own target should be discovered too.

    `primary_protein` targets `metadata.proteins`, whose items each also
    declare a "producer" pid-relation of their own (see
    `internal_relation_nested_model` in conftest.py) - unlike every other
    `internal_relation_*` fixture, whose targets only ever have plain keyword
    keys. This exercises the (otherwise never taken)
    InternalRelationDataType._resolve_nested_relation_fields inner loop that
    turns such a nested relation's own customizations into real relation
    fields, registered here under "metadata.primary_protein.producer".
    """
    record = internal_relation_nested_model.Record(
        {
            "metadata": {
                "proteins": [
                    {"id": "p1", "name": "Protein One", "producer": "some-record-id"},
                ],
                "instruments": [{"id": "i1", "name": "Instrument One"}],
                "primary_protein": {"id": "p1"},
            },
        },
    )

    fields = record.relations._fields
    assert "metadata.primary_protein.producer" in fields

    resolved = getattr(record.relations, "metadata.primary_protein")()
    assert resolved["name"] == "Protein One"
    assert resolved["producer"] == "some-record-id"


def test_internal_relation_ui_marshmallow_dump(
    app,
    identity_simple,
    internal_relation_model,
    search,
    search_clear,
    location,
    db,
    client,
    headers,
):
    """The UI ('vnd.inveniordm.v1+json') response should resolve 'name' via the target's UI schema.

    Exercises LazyInternalUIMarshmallowSchema (create_ui_marshmallow_schema),
    distinct from the "record" marshmallow schema already covered by
    `test_internal_relation_marshmallow_schema` - in particular
    LazyInternalUIMarshmallowSchema._get_target_schema (looked up via the
    model's own RecordUISchema, not the service's record schema) and its
    _missing_field fallback for "id" (which has no UI-specific counterpart -
    mirrors the analogous self-referencing-relation case in
    test_recursive_relations.py).
    """
    res = client.post(
        "/ir-test",
        headers=headers.ui,
        data=json.dumps(
            {
                "files": {"enabled": False},
                "metadata": {
                    "proteins": [{"id": "p1", "name": "Protein One"}],
                    "instruments": [{"id": "i1", "name": "Instrument One"}],
                    "primary_protein": {"id": "p1"},
                },
            },
        ),
    )
    assert res.status_code == 201

    ui = res.json["ui"]
    pp_ui = ui["primary_protein"]
    # "id" has no UI-specific counterpart and falls back to a raw passthrough
    # field (_missing_field) instead of crashing.
    assert pp_ui["id"] == "p1"
    # "name" is a plain keyword with a real UI field on the target's own
    # RecordUISchema, and resolves to its actual (UI-formatted) value.
    assert pp_ui["name"] == "Protein One"


# ============================================================================
# Tests for internal relations with nested keys (e.g., "provider.name")
# ============================================================================


def test_internal_relation_nested_key_mapping_and_jsonschema(app, internal_relation_nested_key_model):
    """The lazily-resolved mapping/json schema should reflect nested target fields like 'provider.name'."""
    m = internal_relation_nested_key_model
    files = m.__files__
    links = m.__symlinks__

    mapping = json.loads(resolve_file_content(files[links["record-mapping-link"]]))
    pp_mapping = mapping["mappings"]["properties"]["metadata"]["properties"]["primary_protein"]

    # Check that nested field provider.name is properly resolved in mapping
    assert pp_mapping["properties"]["id"] == {"type": "keyword", "ignore_above": 256}
    assert pp_mapping["properties"]["name"] == {"type": "keyword", "ignore_above": 256}
    assert pp_mapping["properties"]["provider"] == {
        "type": "object",
        "properties": {"name": {"type": "keyword", "ignore_above": 256}},
    }
    assert "@v" in pp_mapping["properties"]

    jsonschema = json.loads(resolve_file_content(files[links["record-jsonschema-link"]]))
    pp_schema = jsonschema["properties"]["metadata"]["properties"]["primary_protein"]
    assert pp_schema["properties"]["id"] == {"type": "string"}
    assert pp_schema["properties"]["name"] == {"type": "string"}
    # Nested field should be present in JSON schema
    assert pp_schema["properties"]["provider"] == {"type": "object", "properties": {"name": {"type": "string"}}}


@pytest.mark.parametrize(
    ("key", "expected_label"),
    [
        ("name", {"en": "Protein name"}),
        ("provider.name", {"en": "Provider name"}),
    ],
)
def test_internal_relation_nested_key_ui_model(app, internal_relation_nested_key_model, key, expected_label):
    """The lazily-resolved ui model should carry the target's own node for nested keys like 'provider.name'."""
    ui_model = internal_relation_nested_key_model.ui_model
    node = ui_model["children"]["metadata"]["children"]["primary_protein"]
    for part in key.split("."):
        node = node["children"][part]

    # a fallback node would be labelled {"und": <field name>} instead
    assert node["label"] == expected_label


def test_internal_relation_nested_key_marshmallow_schema(app, internal_relation_nested_key_model):
    """LazyInternalMarshmallowSchema should resolve nested 'keys' like 'provider.name'."""
    schema_cls = internal_relation_nested_key_model.proxies.current_service.schema.schema
    field = schema_cls().fields["metadata"].schema.fields["primary_protein"]

    # Test that nested field provider.name is properly included in dump
    dumped = field.schema.dump(
        {"id": "p1", "name": "Protein One", "provider": {"name": "Acme Corp"}, "extra": "dropped"}
    )
    assert dumped == {"id": "p1", "name": "Protein One", "provider": {"name": "Acme Corp"}}


def test_internal_relation_nested_key_field_registered(app, internal_relation_nested_key_model):
    """The InternalRelation system field should be registered with nested keys."""
    from oarepo_runtime.records.systemfields.relations import InternalRelation

    field = internal_relation_nested_key_model.Record.relations._fields["metadata.primary_protein"]
    assert isinstance(field, InternalRelation)
    assert field.target_path == "metadata.proteins"
    # Verify the nested key is part of the field configuration
    assert "provider.name" in field.keys


def test_internal_relation_nested_key_resolve(app, internal_relation_nested_key_model):
    """The relation should resolve nested fields like 'provider.name' correctly."""
    record = internal_relation_nested_key_model.Record(
        {
            "metadata": {
                "proteins": [
                    {"id": "p1", "name": "Protein One", "provider": {"name": "Acme Corp"}},
                    {"id": "p2", "name": "Protein Two", "provider": {"name": "Beta Labs"}},
                ],
                "primary_protein": {"id": "p1"},
            },
        },
    )

    resolved = getattr(record.relations, "metadata.primary_protein")()
    assert resolved["name"] == "Protein One"
    # Verify nested field resolution
    assert resolved["provider"]["name"] == "Acme Corp"


def test_internal_relation_nested_key_service_create_and_search(
    app,
    identity_simple,
    internal_relation_nested_key_model,
    search,
    search_clear,
    location,
    db,
):
    """Internal relation with nested keys should survive the full service create/index/dump cycle.

    This test verifies that nested fields like 'provider.name' are:
    1. Properly dereferenced on create response
    2. Correctly dumped to OpenSearch index
    3. Queryable via search
    """
    Record = internal_relation_nested_key_model.Record
    service = internal_relation_nested_key_model.proxies.current_service

    rec = service.create(
        identity_simple,
        {
            "files": {"enabled": False},
            "metadata": {
                "proteins": [
                    {"id": "p1", "name": "Protein One", "provider": {"name": "Acme Corp"}},
                    {"id": "p2", "name": "Protein Two", "provider": {"name": "Beta Labs"}},
                ],
                "primary_protein": {"id": "p1"},
            },
        },
    )

    md = rec.data["metadata"]
    # Verify basic fields
    assert md["primary_protein"]["id"] == "p1"
    assert md["primary_protein"]["name"] == "Protein One"
    # Verify nested field is dereferenced
    assert md["primary_protein"]["provider"]["name"] == "Acme Corp"

    # Refresh to make changes live
    Record.index.refresh()

    # Query by nested field - this confirms the nested value was dumped to index
    hits = service.search(identity_simple, q='metadata.primary_protein.provider.name:"Acme Corp"', size=25, page=1)
    assert hits.total == 1, (
        f"Expected 1 hit for 'Acme Corp', got {hits.total}. "
        "This test exposes whether nested internal relation fields are dumped correctly."
    )
    assert next(iter(hits.hits))["id"] == rec.id

    # Query for the other protein's provider - should not match
    no_hits = service.search(identity_simple, q='metadata.primary_protein.provider.name:"Beta Labs"', size=25, page=1)
    assert no_hits.total == 0


@pytest.mark.parametrize(
    ("relation", "expected_label"),
    [
        # target path metadata.general.proteins: `general` is a named type (General),
        # its `proteins` items are a named type (Protein)
        ("primary_protein", {"en": "Protein name"}),
        # target path metadata.general.entities: items are a named polymorphic type
        # (Entity) whose variants are named types
        ("primary_entity", {"en": "Entity name"}),
    ],
)
def test_internal_relation_named_types_ui_model(app, internal_relation_named_types_model, relation, expected_label):
    """Relation keys must be resolved through named types, as real models write them.

    The target path of an internal relation is walked through the model's declarative
    types. A node like `{"type": "General"}` refers to a named type and has no inline
    "properties"; the walk must follow the reference (and, for a polymorphic type, merge
    its variants) instead of failing with "oneOf must be a list" and falling back to a
    generic key, which shows up here as the label {"und": "name"}.
    """
    ui_model = internal_relation_named_types_model.ui_model
    node = ui_model["children"]["metadata"]["children"][relation]["children"]["name"]

    # a fallback node would be labelled {"und": "name"} instead
    assert node["label"] == expected_label


# ---------------------------------------------------------------------------
# lazy structures combined with polymorphic types
# ---------------------------------------------------------------------------


def test_internal_relation_named_types_nested_relation_registered(app, internal_relation_named_types_model):
    """A relation inside the keys of an internal relation behind a named type is discovered.

    Pattern: test_internal_relation_nested_relation_field_registered, but the
    target path (metadata.general.proteins) crosses the named type General.
    The declarative walk must follow the reference - otherwise the nested
    'language' vocabulary relation is never registered on record.relations
    (and a "Failed to resolve target properties" warning is logged instead).
    """
    record = internal_relation_named_types_model.Record({"metadata": {}})
    assert "metadata.primary_protein_full.language" in record.relations._fields


def test_internal_relation_named_types_no_target_properties_warning(app, internal_relation_named_types_model, caplog):
    """The named-type-following walk must not log the 'Failed to resolve' warning."""
    with caplog.at_level("WARNING", logger="oarepo_model"):
        fields = internal_relation_named_types_model.Record({"metadata": {}}).relations._fields
    assert fields
    assert not [r for r in caplog.records if "Failed to resolve target properties" in r.message]


def test_polymorphic_variant_containing_internal_relation_builds_and_resolves(app, internal_relation_named_types_model):
    """An internal relation nested inside a polymorphic variant resolves at runtime.

    The model build must not resolve the relation's lazy UI model while merging
    the variants' children (the model is still being built - the merge keeps
    such nodes opaque), and a real record must dereference the relation stored
    inside the variant the same as anywhere else.
    """
    m = internal_relation_named_types_model

    # ui model merged across the two variants carries the relation node lazily,
    # and the exact per-variant models are reachable too
    mixed = m.ui_model["children"]["metadata"]["children"]["mixed_entries"]
    assert set(mixed["child"]["variants"]) == {"sample", "reference"}

    record = m.Record(
        {
            "metadata": {
                "general": {
                    "proteins": [{"id": "p1", "name": "Hemoglobin"}],
                },
                "mixed_entries": [
                    {
                        "entry_type": "sample",
                        "label": "Sample 1",
                        "related_protein": {"id": "p1"},
                    }
                ],
            },
        },
    )

    # the relation lives one array level deep (mixed_entries items): the result
    # is an iterator over the array's resolved relation values
    resolved = getattr(record.relations, "metadata.mixed_entries.related_protein")()
    assert next(iter(resolved))["name"] == "Hemoglobin"


def test_internal_relation_key_path_through_polymorphic_variant(app, internal_relation_named_types_model):
    """A relation key reaching inside a polymorphic variant (details.code) resolves.

    'details' is polymorphic inside the entities' variants; the lazy UI model,
    marshmallow schema and dereference machinery must merge the variants to
    find 'code', not stop at the polymorphic node.
    """
    m = internal_relation_named_types_model

    # the ui model of the relation key resolves the label through the
    # polymorphic 'details' node (the fallback would show {"und": "code"})
    node = m.ui_model["children"]["metadata"]["children"]["primary_entity_detail"]
    assert node["children"]["details"]["children"]["code"]["label"] == {"en": "Gene code"}

    record = m.Record(
        {
            "metadata": {
                "general": {
                    "entities": [
                        {
                            "id": "e1",
                            "entity_type": "person",
                            "name": "Insulin",
                            "details": {"details_type": "gene", "code": "INS"},
                        }
                    ],
                },
                "primary_entity_detail": {"id": "e1"},
            },
        },
    )

    resolved = getattr(record.relations, "metadata.primary_entity_detail")()
    assert resolved["details"]["code"] == "INS"


def test_polymorphic_ui_model_does_not_resolve_relation_nested_inside_variant(
    build_internal_relation_nested_in_variant_model,
):
    """Building the UI model must not resolve a lazy relation nested deep inside a variant.

    `BindingResult.proteins_involved[].protein` is an
    internal relation whose UI model is a lazy ReferenceUIModel three levels below the variant
    child (`proteins_involved` -> `child` -> `children.protein`), as in mbdb's
    `Result.entities_involved[].entity`. Shrinking the per-variant UI models to their
    differences compared these children with `==`. Dict equality descends into the lazy node,
    which resolves it by importing the model that is still being built, so the build fails
    with ModuleNotFoundError. A relation placed *directly* under the variant does not show the
    bug (see test_polymorphic_variant_containing_internal_relation_builds_and_resolves),
    because the top-level isinstance(node, dict) guard skips the comparison there.
    """
    model = build_internal_relation_nested_in_variant_model()

    results = model.ui_model["children"]["metadata"]["children"]["results"]["child"]
    # the union carries the nested relation node (still unresolved, so only check presence)
    proteins_involved = results["children"]["proteins_involved"]
    assert "protein" in proteins_involved["child"]["children"]
    # the variant that declares the field keeps it: a lazy node can not be compared without
    # resolving it, so it never counts as "identical to the union"
    assert "proteins_involved" in results["variants"]["binding"]["children"]
