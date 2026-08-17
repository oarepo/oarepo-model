#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
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

    mapping = json.loads(resolve_file_content(m.__files__["internal/primary_mapping.json"]))
    pp_mapping = mapping["mappings"]["properties"]["metadata"]["properties"]["primary_protein"]
    assert pp_mapping["properties"]["id"] == {"type": "keyword", "ignore_above": 256}
    assert pp_mapping["properties"]["name"] == {"type": "keyword", "ignore_above": 256}
    assert "@v" in pp_mapping["properties"]

    jsonschema = json.loads(resolve_file_content(m.__files__["internal/primary_jsonschema.json"]))
    pp_schema = jsonschema["properties"]["metadata"]["properties"]["primary_protein"]
    assert pp_schema["properties"]["id"] == {"type": "string"}
    assert pp_schema["properties"]["name"] == {"type": "string"}


def test_internal_relation_marshmallow_schema(app, internal_relation_model):
    """LazyInternalMarshmallowSchema should resolve 'keys' against the target's real fields."""
    schema_cls = internal_relation_model.proxies.current_service.schema.schema
    field = schema_cls().fields["metadata"].schema.fields["primary_protein"]

    # LazyProxiedMarshmallowSchema (see relations.py) only builds/exposes its
    # real fields lazily on load()/dump() - .fields itself stays empty by
    # design (mirrors LazyMarshmallowSchema's own behaviour for pid-relation).
    dumped = field.schema.dump({"id": "p1", "name": "Protein One", "extra": "dropped"})
    assert dumped == {"id": "p1", "name": "Protein One"}


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
    assert field.target_paths == ["metadata.proteins"]


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
        hits = service.search(
            identity_simple, q=f'metadata.used_instruments.name:"{instrument_name}"', size=25, page=1
        )
        assert hits.total == 1, (
            f"Expected 1 hit for {instrument_name}, got {hits.total}. "
            "This test exposes whether array internal relations are dumped correctly."
        )
        assert next(iter(hits.hits))["id"] == rec.id

    # Query for an instrument name that is in the record but NOT in the relation
    no_hits = service.search(
        identity_simple, q='metadata.used_instruments.name:"Microscope B"', size=25, page=1
    )
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
    id that doesn't exist in any of the field's target_paths.
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
    hits = service.search(
        identity_simple, q='metadata.primary_protein.name:"Brand New Protein"', size=25, page=1
    )
    assert hits.total == 1, (
        f"Expected 1 hit for 'Brand New Protein', got {hits.total}. "
        "This test exposes whether internal relations are dumped to OpenSearch correctly."
    )
    assert next(iter(hits.hits))["id"] == rec.id
