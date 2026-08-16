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

from oarepo_model.utils import resolve_file_content


def test_internal_relation_mapping_and_jsonschema(app, internal_relation_model):
    """The lazily-resolved mapping/json schema should reflect the target_paths' real fields."""
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
    """LazyInternalMarshmallowSchema should resolve 'keys' against the target_paths' real fields."""
    schema_cls = internal_relation_model.proxies.current_service.schema.schema
    field = schema_cls().fields["metadata"].schema.fields["primary_protein"]

    # LazyProxiedMarshmallowSchema (see relations.py) only builds/exposes its
    # real fields lazily on load()/dump() - .fields itself stays empty by
    # design (mirrors LazyMarshmallowSchema's own behaviour for pid-relation).
    dumped = field.schema.dump({"id": "p1", "name": "Protein One", "extra": "dropped"})
    assert dumped == {"id": "p1", "name": "Protein One"}


def test_internal_relation_ui_model(app, internal_relation_model):
    """LazyInternalUIModelChildren should resolve 'keys' against the target_paths' real ui model."""
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
    assert field.target_paths == ["metadata.proteins", "metadata.instruments"]


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
