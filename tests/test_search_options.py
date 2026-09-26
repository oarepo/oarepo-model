# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Draft and record search options must run the same parameter interpreters.

The interpreters registered on `extra_param_interpreter_classes` (the geo ones by
`GeoPreset`) are consumed by both `RecordSearchOptions` and `DraftSearchOptions`;
draft search is the same query language as record search, so anything registered
must be honoured by both.
"""

from __future__ import annotations

import inspect

from oarepo_runtime.services.facets.params import GroupedFacetsParam

from oarepo_model.api import model
from oarepo_model.presets.drafts import drafts_preset
from oarepo_model.presets.records_resources import records_resources_preset
from oarepo_model.presets.records_resources.services.records.params.spherical import (
    GeoDistanceParam,
)


def _model(name: str):
    return model(
        name=name,
        version="1.0.0",
        presets=[records_resources_preset, drafts_preset],
        types=[{"Metadata": {"properties": {"title": {"type": "keyword"}}}}],
        metadata_type="Metadata",
    )


def test_draft_and_record_search_options_resolve_the_same_interpreters():
    """Apart from the drafts' own AllVersionsParam, both must run the same interpreters."""
    m = _model("search_options_same_interpreters")

    record = m.RecordSearchOptions().params_interpreters_cls
    draft = [clazz for clazz in m.DraftSearchOptions().params_interpreters_cls if inspect.isclass(clazz)]

    assert draft == record


def test_geo_interpreters_are_registered_on_draft_search_options():
    m = _model("search_options_draft_geo")

    extra = m.RecordSearchOptions().extra_param_interpreter_classes
    assert GeoDistanceParam in extra, "the test model must actually register extra interpreters"

    draft = m.DraftSearchOptions().params_interpreters_cls
    assert set(extra) <= set(draft)


def test_extra_interpreters_run_before_the_facets_interpreter():
    m = _model("search_options_interpreter_order")

    for options in (m.RecordSearchOptions(), m.DraftSearchOptions()):
        classes = options.params_interpreters_cls
        assert classes.index(GeoDistanceParam) < classes.index(GroupedFacetsParam)
