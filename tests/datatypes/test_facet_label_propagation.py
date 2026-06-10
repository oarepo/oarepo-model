#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest


class TestArrayFacetLabelPropagation:
    """Tests that ArrayDataType propagates the array element's label to items facet generation."""

    @pytest.fixture
    def array_type(self, datatype_registry):
        return datatype_registry.get_type("array")

    @pytest.fixture
    def keyword_type(self, datatype_registry):
        return datatype_registry.get_type("keyword")

    def test_array_label_propagates_to_items(self, array_type, keyword_type):
        """When array has a label and items do not, the label is propagated to items."""
        mock_get_facet = MagicMock(return_value={})
        original_get_facet = keyword_type.get_facet
        keyword_type.get_facet = mock_get_facet

        try:
            element = {
                "type": "array",
                "items": {"type": "keyword"},
                "label": {"en": "Languages", "cs": "Jazyky"},
            }
            facets: dict[str, list] = {}
            array_type.get_facet("languages", element, [], facets)

            assert mock_get_facet.call_count == 1
            call_args = mock_get_facet.call_args
            passed_element = call_args.kwargs.get("element") or call_args.args[1]
            assert passed_element.get("label") == {"en": "Languages", "cs": "Jazyky"}
        finally:
            keyword_type.get_facet = original_get_facet

    def test_items_label_takes_priority(self, array_type, keyword_type):
        """When items already has a label, the array label should not overwrite it."""
        mock_get_facet = MagicMock(return_value={})
        original_get_facet = keyword_type.get_facet
        keyword_type.get_facet = mock_get_facet

        try:
            element = {
                "type": "array",
                "items": {
                    "type": "keyword",
                    "label": {"en": "Item Label", "cs": "Položka"},
                },
                "label": {"en": "Array Label", "cs": "Pole"},
            }
            facets: dict[str, list] = {}
            array_type.get_facet("languages", element, [], facets)

            assert mock_get_facet.call_count == 1
            call_args = mock_get_facet.call_args
            passed_element = call_args.kwargs.get("element") or call_args.args[1]
            assert passed_element.get("label") == {"en": "Item Label", "cs": "Položka"}
        finally:
            keyword_type.get_facet = original_get_facet

    def test_no_label_means_no_propagation(self, array_type, keyword_type):
        """When array has no label, items should not receive any label."""
        mock_get_facet = MagicMock(return_value={})
        original_get_facet = keyword_type.get_facet
        keyword_type.get_facet = mock_get_facet

        try:
            element = {
                "type": "array",
                "items": {"type": "keyword"},
            }
            facets: dict[str, list] = {}
            array_type.get_facet("languages", element, [], facets)

            assert mock_get_facet.call_count == 1
            call_args = mock_get_facet.call_args
            passed_element = call_args.kwargs.get("element") or call_args.args[1]
            assert "label" not in passed_element
        finally:
            keyword_type.get_facet = original_get_facet

    def test_original_array_element_not_mutated(self, array_type, keyword_type):
        """The label propagation must not mutate the original element dict."""
        mock_get_facet = MagicMock(return_value={})
        original_get_facet = keyword_type.get_facet
        keyword_type.get_facet = mock_get_facet

        try:
            element = {
                "type": "array",
                "items": {"type": "keyword"},
                "label": {"en": "Languages"},
            }
            original_items = element["items"].copy()
            facets: dict[str, list] = {}
            array_type.get_facet("languages", element, [], facets)

            assert element["items"] == original_items
            assert "label" not in element["items"]
        finally:
            keyword_type.get_facet = original_get_facet
