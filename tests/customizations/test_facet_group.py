#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations import AddFacetGroup
from oarepo_model.errors import AlreadyRegisteredError


def test_add_facet_group_defaults_drafts_to_facets():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)

    AddFacetGroup("default", ["metadata.a", "metadata.b"]).apply(builder, model)

    assert builder.get_dictionary("FacetGroups")["default"] == ["metadata.a", "metadata.b"]
    assert builder.get_dictionary("DraftFacetGroups")["default"] == ["metadata.a", "metadata.b"]


def test_add_facet_group_with_explicit_draft_facets():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)

    AddFacetGroup(
        "curator",
        ["metadata.a"],
        draft_facets=["metadata.a", "metadata.draft_only"],
    ).apply(builder, model)

    assert builder.get_dictionary("FacetGroups")["curator"] == ["metadata.a"]
    assert builder.get_dictionary("DraftFacetGroups")["curator"] == [
        "metadata.a",
        "metadata.draft_only",
    ]


def test_add_facet_group_duplicate_raises():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)

    AddFacetGroup("default", ["metadata.a"]).apply(builder, model)

    with pytest.raises(AlreadyRegisteredError, match="Facet group default already exists"):
        AddFacetGroup("default", ["metadata.b"]).apply(builder, model)


def test_add_facet_group_exists_ok_overwrites():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)

    AddFacetGroup("default", ["metadata.a"]).apply(builder, model)
    AddFacetGroup("default", ["metadata.b"], exists_ok=True).apply(builder, model)

    assert builder.get_dictionary("FacetGroups")["default"] == ["metadata.b"]
    assert builder.get_dictionary("DraftFacetGroups")["default"] == ["metadata.b"]
