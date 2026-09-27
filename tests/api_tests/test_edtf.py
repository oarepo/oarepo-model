# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""EDTF-based types: what validates must also index.

An interval is stored as a keyword, and must be range-queryable via the
sibling date_range field the dumper extension writes.
"""

from __future__ import annotations

import pytest
from marshmallow.exceptions import ValidationError


def _create(edtf_model, identity_simple, metadata):
    service = edtf_model.proxies.current_service
    return service.create(identity_simple, {"metadata": {"title": "T", **metadata}})


def test_edtf_interval_indexes_and_dumps_a_sibling_range(
    app,
    edtf_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    """An interval string itself is not parseable by OpenSearch.

    It must land in the index via the ``<field>_range`` sibling written by the
    dumper extension instead.
    """
    record = _create(edtf_model, identity_simple, {"interval": "1964/2008"})
    edtf_model.Record.index.refresh()

    # the indexed document (the record's dump towards OpenSearch)
    hit = next(iter(edtf_model.Record.index.search().query("term", id=record.id)))
    source = hit.to_dict()
    assert source["metadata"]["interval"] == "1964/2008"
    assert source["metadata"]["interval_range"] == {
        "gte": "1964-01-01",
        "lte": "2008-12-31",
    }

    # and is found by a range query against that sibling field
    hits = edtf_model.Record.index.search().query(
        "range",
        **{"metadata.interval_range": {"gte": "1980-01-01", "lte": "1980-12-31"}},
    )
    assert hits.count() == 1

    # loading back strips the generated sibling again
    loaded = edtf_model.proxies.current_service.read(identity_simple, record.id)
    assert loaded.data["metadata"]["interval"] == "1964/2008"
    assert "interval_range" not in loaded.data["metadata"]


def test_value_crashing_the_edtf_library_is_rejected_politely(
    app,
    edtf_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    """A season crashes the edtf library on its own - rejected as a client error."""
    with pytest.raises(ValidationError):
        _create(edtf_model, identity_simple, {"date": "2001-21"})


def test_naive_datetime_is_indexed_as_utc(
    app,
    edtf_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    """A datetime without an offset is appended Z for indexing and is searchable."""
    record = _create(edtf_model, identity_simple, {"datetime": "2024-01-01T12:30:00"})
    edtf_model.Record.index.refresh()

    hit = next(iter(edtf_model.Record.index.search().query("term", id=record.id)))
    assert hit.to_dict()["metadata"]["datetime"] == "2024-01-01T12:30:00Z"

    hits = edtf_model.Record.index.search().query(
        "range",
        **{"metadata.datetime": {"gte": "2024-01-01T00:00:00Z", "lte": "2024-01-01T23:59:59Z"}},
    )
    assert hits.count() == 1

    # the record itself (loaded from the database, not the index) stays as typed
    loaded = edtf_model.proxies.current_service.read(identity_simple, record.id)
    assert loaded.data["metadata"]["datetime"] == "2024-01-01T12:30:00"


@pytest.mark.parametrize("field", ["date", "datetime"])
@pytest.mark.parametrize("value", ["19XX", "-1997", "2023-XX"])
def test_parseable_dates_opensearch_cannot_index_stay_stored_but_unsearchable(
    app,
    edtf_model,
    identity_simple,
    search,
    search_clear,
    location,
    field,
    value,
):
    """EDTF-valid dates unknown to OpenSearch still index (ignore_malformed).

    The original stays in _source; the date is simply not found by date queries.
    """
    record = _create(edtf_model, identity_simple, {field: value})
    edtf_model.Record.index.refresh()

    hit = next(iter(edtf_model.Record.index.search()))
    assert hit.to_dict()["metadata"][field] == value

    # broad value-agnostic date queries find nothing through the date field
    assert (
        edtf_model.Record.index.search()
        .query("range", **{f"metadata.{field}": {"gte": "1000-01-01", "lte": "9999-12-31"}})
        .count()
        == 0
    )
    assert edtf_model.proxies.current_service.read(identity_simple, record.id).data["metadata"][field] == value


def test_level_zero_forms_index_fine(
    app,
    edtf_model,
    identity_simple,
    search,
    search_clear,
    location,
):
    """The accepted forms: yyyy, yyyy-MM, yyyy-MM-DD, datetime with an offset."""
    _create(
        edtf_model,
        identity_simple,
        {
            "date": "2024",
            "datetime": "2024-01-01T00:00:00Z",
            "interval": "2024-01/2024-06",
        },
    )
    _create(edtf_model, identity_simple, {"date": "2024-02-29", "datetime": "2024-01-01T00:00:00+02:00"})
    edtf_model.Record.index.refresh()
    assert edtf_model.Record.index.search().count() == 2
