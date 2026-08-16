#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations


def test_relations(
    app,
    identity_simple,
    empty_model,
    relation_model,
    search,
    search_clear,
    location,
):
    TargetRecord = empty_model.Record
    target_service = empty_model.proxies.current_service

    # Create the target records

    rec1_id = target_service.create(
        identity_simple,
        {"files": {"enabled": False}, "metadata": {"title": "Record 1"}},
    ).id
    rec2_id = target_service.create(
        identity_simple,
        {"files": {"enabled": False}, "metadata": {"title": "Record 2"}},
    ).id
    rec3_id = target_service.create(
        identity_simple,
        {"files": {"enabled": False}, "metadata": {"title": "Record 3"}},
    ).id

    # Refresh to make changes live
    TargetRecord.index.refresh()

    relation_service = relation_model.proxies.current_service

    relation_rec = relation_service.create(
        identity_simple,
        {
            "files": {
                "enabled": False,
            },
            "metadata": {
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


def test_relation_facets(app, relation_model):
    """Check that facets are generated for a pid-relation's 'keys'.

    Facet generation (MetadataFacetsPreset/RecordFacetsPreset -> get_facets
    -> DataType.get_facet) walks the *local* schema tree, calling
    `self._registry.get_type(value).get_facet(...)` recursively for object/
    array content (see ObjectDataType.get_facet, ArrayDataType.get_facet).
    PIDRelation.get_facet mirrors that recursion via _get_properties() (see
    its docstring in datatypes/relations.py) - so a relation's individual
    "keys" (e.g. "id", "metadata.title") get their own facet, whether the
    relation is a plain field ("direct"), nested in an array ("array"), or
    nested inside a plain object field ("object.a"). For the
    self-referencing case, see test_recursive_relations_facets in
    test_recursive_relations.py - the target's real schema isn't known yet
    at facet-generation (build) time, so no facets are generated there.
    """
    facets = relation_model.facets

    for base in ("metadata.direct", "metadata.array", "metadata.object.a"):
        # "id" (a plain keyword key) should get its own terms facet.
        assert hasattr(facets, f"{base}.id"), f"missing facet for {base}.id"
        # "metadata.title" resolves (see PIDRelation._get_properties) to the
        # target's real "fulltext+keyword" type, which is itself facetable.
        assert hasattr(facets, f"{base}.metadata.title"), f"missing facet for {base}.metadata.title"
