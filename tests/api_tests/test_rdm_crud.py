#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from io import BytesIO

import pytest
from invenio_pidstore.errors import PIDDeletedError, PIDDoesNotExistError


def test_finalization_called(app, rdm_model, finalization_called):
    assert finalization_called.called


def test_simple_flow(
    app,
    test_rdm_service,
    identity_simple,
    input_data,
    rdm_model,
    search,
    search_clear,
    location,
):
    Draft = rdm_model.Draft

    # Create an item
    item = test_rdm_service.create(identity_simple, input_data)
    id_ = item.id

    # Read it
    read_item = test_rdm_service.read_draft(identity_simple, id_)
    assert item.id == read_item.id

    # Refresh to make changes live
    Draft.index.refresh()

    # Search it
    res = test_rdm_service.search_drafts(identity_simple, q=f"id:{id_}", size=25, page=1)
    assert res.total == 1
    first_hit = next(iter(res.hits))
    assert first_hit["metadata"] == read_item.data["metadata"]
    assert first_hit["links"].items() <= read_item.links.items()

    # Update it
    data = read_item.data
    data["metadata"]["title"] = "New title"
    update_item = test_rdm_service.update_draft(identity_simple, id_, data)
    assert item.id == update_item.id
    assert update_item["metadata"]["title"] == "New title"

    # Can not publish as publishing needs files support in drafts

    test_rdm_service.delete_draft(identity_simple, id_)
    Draft.index.refresh()

    # Retrieve it - deleted so cannot
    # - db
    pytest.raises(PIDDoesNotExistError, test_rdm_service.read, identity_simple, id_)
    # - search
    res = test_rdm_service.search(identity_simple, q=f"id:{id_}", size=25, page=1)
    assert res.total == 0


def add_file_to_draft(service, draft_id, file_id, identity):
    """Add a file to the record."""
    result = service.init_files(identity, draft_id, data=[{"key": file_id}])
    file_md = next(iter(result.entries))
    assert file_md["key"] == "test.txt"
    assert file_md["status"] == "pending"

    service.set_file_content(identity, draft_id, file_id, BytesIO(b"test file content"))
    result = service.commit_file(identity, draft_id, file_id)
    file_md = result.data
    assert file_md["status"] == "completed"
    return result


def test_publish(
    app,
    test_rdm_service,
    test_rdm_draft_files_service,
    identity_simple,
    input_data,
    rdm_model,
    search,
    search_clear,
    location,
):
    Record = rdm_model.Record
    Draft = rdm_model.Draft

    # Create an item
    item = test_rdm_service.create(identity_simple, input_data)
    id_ = item.id
    Draft.index.refresh()

    # Add a file
    add_file_to_draft(test_rdm_draft_files_service, id_, "test.txt", identity_simple)

    # Can not publish as publishing needs files support in drafts
    test_rdm_service.publish(identity_simple, id_)

    test_rdm_service.delete(identity_simple, id_)
    Record.index.refresh()

    # Retrieve it - deleted so cannot
    # - db
    pytest.raises(PIDDeletedError, test_rdm_service.read, identity_simple, id_)
    # - search
    res = test_rdm_service.search(identity_simple, q=f"id:{id_}", size=25, page=1)
    assert res.total == 0


def test_rdm_publish(
    app,
    test_rdm_service,
    test_rdm_draft_files_service,
    identity_simple,
    input_data,
    rdm_model,
    add_file_to_draft,
    search,
    search_clear,
    location,
):
    Record = rdm_model.Record
    Draft = rdm_model.Draft

    # Create an item
    item = test_rdm_service.create(identity_simple, input_data)
    id_ = item.id
    Draft.index.refresh()

    # Add a file
    add_file_to_draft(test_rdm_draft_files_service, id_, "test.txt", identity_simple)

    # Can not publish as publishing needs files support in drafts
    test_rdm_service.publish(identity_simple, id_)

    test_rdm_service.delete(identity_simple, id_)
    Record.index.refresh()

    # Retrieve it - deleted so cannot
    # - db
    pytest.raises(PIDDeletedError, test_rdm_service.read, identity_simple, id_)
    # - search
    res = test_rdm_service.search(identity_simple, q=f"id:{id_}", size=25, page=1)
    assert res.total == 0
