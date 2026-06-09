#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from oarepo_model.datatypes.collections import ArrayDataType
from oarepo_model.datatypes.registry import DataTypeRegistry


def test_array_facet_label_propagation():
    """Test that array element labels are propagated to items for facet generation."""
    registry = DataTypeRegistry()
    registry.load_entry_points()

    array_type = ArrayDataType(registry)

    array_element = {
        "type": "array",
        "label": {"en": "Languages", "cs": "Jazyky"},
        "items": {
            "type": "vocabulary",
            "vocabulary-type": "languages",
        },
    }

    facets = {}
    result = array_type.get_facet("metadata.languages", array_element, [], facets)

    # The facet should have been generated
    assert "metadata.languages" in result
    
    # The label should be propagated to the items element.
    # FacetMixin.get_facet passes label=element.get("label") to get_basic_facet
    # when the element has a label. Since our fix propagates the array's label
    # to the items dict, the generated facet should contain the label.
    facet_def = result["metadata.languages"]
    leaf = facet_def[-1]
    assert leaf.get("label") == {"en": "Languages", "cs": "Jazyky"}


def test_array_facet_label_with_keyword_items():
    """Test that array labels propagate to keyword item facets."""
    registry = DataTypeRegistry()
    registry.load_entry_points()

    array_type = ArrayDataType(registry)

    array_element = {
        "type": "array",
        "label": {"en": "Keywords", "cs": "Klíčová slova"},
        "items": {
            "type": "keyword",
        },
    }

    facets = {}
    result = array_type.get_facet("metadata.keywords", array_element, [], facets)

    assert "metadata.keywords" in result
    facet_def = result["metadata.keywords"]
    leaf = facet_def[-1]
    assert leaf.get("label") == {"en": "Keywords", "cs": "Klíčová slova"}


def test_array_facet_does_not_override_item_label():
    """Test that item labels are not overridden by array labels."""
    registry = DataTypeRegistry()
    registry.load_entry_points()

    array_type = ArrayDataType(registry)

    array_element = {
        "type": "array",
        "label": {"en": "Array Label"},
        "items": {
            "type": "keyword",
            "label": {"en": "Item Label"},
        },
    }

    facets = {}
    result = array_type.get_facet("metadata.array", array_element, [], facets)

    facet_def = result["metadata.array"]
    leaf = facet_def[-1]
    # Item label should take precedence
    assert leaf.get("label") == {"en": "Item Label"}
