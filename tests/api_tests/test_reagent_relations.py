#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for a pid-relation whose copied 'keys' subtree itself contains a vocabulary field.

Model B (`reagent_model`) has `metadata.reagent`, a plain object with a
`chemical` vocabulary field (`vocabulary-type: chemicals`) next to a plain
`concentration` number. Model A (`reagent_relation_model`) has a
`metadata.b` pid-relation to B with `keys: ["id", "metadata.reagent"]` - i.e.
it pulls in the *whole* `reagent` subtree, not just a couple of scalar keys.

This exercises PIDRelation._get_properties resolving a dotted key to a
non-leaf ("object") property copied wholesale from the target's real schema
(see resolve_declared_root_properties/_lookup_property in relations.py), and
confirms the nested vocabulary relation inside that copied subtree is still
discovered and dereferenced on dump (via the same nested-relation-discovery
walk used for nested pid-relations elsewhere, e.g.
test_internal_relations.py::test_internal_relation_nested_relation_field_registered)
- not just the plain 'concentration' sibling.
"""

from __future__ import annotations


def test_reagent_relation_dumps_chemical_and_concentration(
    app,
    identity_simple,
    reagent_model,
    reagent_relation_model,
    vocabulary_fixtures,
    search,
    search_clear,
    location,
    db,
):
    b_service = reagent_model.proxies.current_service

    b_rec = b_service.create(
        identity_simple,
        {
            "files": {"enabled": False},
            "metadata": {
                "reagent": {
                    "chemical": {"id": "c1"},
                    "concentration": 23.5,
                },
            },
        },
    )
    b_id = b_rec.id

    reagent_model.Record.index.refresh()

    a_service = reagent_relation_model.proxies.current_service

    a_rec = a_service.create(
        identity_simple,
        {
            "files": {"enabled": False},
            "metadata": {
                "b": {"id": b_id},
            },
        },
    )

    b = a_rec.data["metadata"]["b"]
    assert b["id"] == b_id

    reagent = b["metadata"]["reagent"]
    assert reagent["concentration"] == 23.5
    assert reagent["chemical"]["id"] == "c1"
    assert reagent["chemical"]["props"] == {
        "inchi": "InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)",
    }
