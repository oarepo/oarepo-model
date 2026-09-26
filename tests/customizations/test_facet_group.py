# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations import AddFacetGroup
from oarepo_model.errors import AlreadyRegisteredError, PartialNotFoundError


def _facet_builder() -> tuple[InvenioModelBuilder, MagicMock]:
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    builder.add_dictionary("FacetGroups")
    builder.add_dictionary("DraftFacetGroups")
    return builder, model


def test_add_facet_group_missing_dictionaries_raise():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)

    with pytest.raises(PartialNotFoundError, match="FacetGroups"):
        AddFacetGroup("default", ["metadata.a"]).apply(builder, model)


def test_add_facet_group_missing_draft_dictionaries_raise():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    builder.add_dictionary("FacetGroups")

    with pytest.raises(PartialNotFoundError, match="DraftFacetGroups"):
        AddFacetGroup("default", ["metadata.a"]).apply(builder, model)


def test_add_facet_group_defaults_drafts_to_facets():
    builder, model = _facet_builder()

    AddFacetGroup("default", ["metadata.a", "metadata.b"]).apply(builder, model)

    assert builder.get_dictionary("FacetGroups")["default"] == ["metadata.a", "metadata.b"]
    assert builder.get_dictionary("DraftFacetGroups")["default"] == ["metadata.a", "metadata.b"]


def test_add_facet_group_with_explicit_draft_facets():
    builder, model = _facet_builder()

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
    builder, model = _facet_builder()

    AddFacetGroup("default", ["metadata.a"]).apply(builder, model)

    with pytest.raises(AlreadyRegisteredError, match="Facet group default already exists"):
        AddFacetGroup("default", ["metadata.b"]).apply(builder, model)


def test_add_facet_group_exists_ok_overwrites():
    builder, model = _facet_builder()

    AddFacetGroup("default", ["metadata.a"]).apply(builder, model)
    AddFacetGroup("default", ["metadata.b"], exists_ok=True).apply(builder, model)

    assert builder.get_dictionary("FacetGroups")["default"] == ["metadata.b"]
    assert builder.get_dictionary("DraftFacetGroups")["default"] == ["metadata.b"]
