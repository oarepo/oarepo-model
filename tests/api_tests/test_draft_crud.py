#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import json
from io import BytesIO

import pytest
from invenio_pidstore.errors import PIDDeletedError, PIDDoesNotExistError


def test_simple_flow(
    app,
    test_draft_service,
    identity_simple,
    input_data_with_files_disabled,
    draft_model,
    search,
    search_clear,
    location,
):
    Draft = draft_model.Draft

    # Create an item
    item = test_draft_service.create(identity_simple, input_data_with_files_disabled)
    id_ = item.id

    # Read it
    read_item = test_draft_service.read_draft(identity_simple, id_)
    assert item.id == read_item.id
    assert item.data == read_item.data

    # Refresh to make changes live
    Draft.index.refresh()

    # Search it
    res = test_draft_service.search_drafts(
        identity_simple,
        q=f"id:{id_}",
        size=25,
        page=1,
    )
    assert res.total == 1
    first_hit = next(iter(res.hits))
    assert first_hit["metadata"] == read_item.data["metadata"]
    assert first_hit["links"].items() <= read_item.links.items()

    # Update it
    data = read_item.data
    data["metadata"]["title"] = "New title"
    update_item = test_draft_service.update_draft(identity_simple, id_, data)
    assert item.id == update_item.id
    assert update_item["metadata"]["title"] == "New title"

    # Can not publish as publishing needs files support in drafts

    test_draft_service.delete_draft(identity_simple, id_)
    Draft.index.refresh()

    # Retrieve it - deleted so cannot
    # - db
    pytest.raises(PIDDoesNotExistError, test_draft_service.read, identity_simple, id_)
    # - search
    res = test_draft_service.search(identity_simple, q=f"id:{id_}", size=25, page=1)
    assert res.total == 0


def test_simple_flow_resource(
    app,
    client,
    draft_model,
    search,
    search_clear,
    location,
    headers,
    input_data_more_complex,
):
    Draft = draft_model.Draft

    # Create a draft
    res = client.post("/draft-test", headers=headers.json, data=json.dumps(input_data_more_complex))
    assert res.status_code == 201
    id_ = res.json["id"]
    assert res.json["metadata"] == input_data_more_complex["metadata"]

    # Check for UI representation values
    # TODO: for some reason there is no is_draft field on a record
    res = client.get(f"/draft-test/{id_}/draft", headers=headers.ui)
    assert res.status_code == 200
    assert set(res.json["ui"].keys()) == {
        "created_date_l10n_short",
        "created_date_l10n_medium",
        "created_date_l10n_long",
        "created_date_l10n_full",
        "updated_date_l10n_short",
        "updated_date_l10n_medium",
        "updated_date_l10n_long",
        "updated_date_l10n_full",
        "some_bool_val_i18n",
        "height",
        "is_draft",
    }
    assert res.json["ui"]["some_bool_val_i18n"] == "true"
    assert res.json["ui"]["height"] == "123"

    Draft.index.refresh()

    # Search it
    res = client.get("/user/draft-test", query_string={"q": f"id:{id_}"}, headers=headers.json)
    assert res.status_code == 200
    assert res.json["hits"]["total"] == 1
    assert res.json["hits"]["hits"][0]["metadata"] == input_data_more_complex["metadata"]
    data = res.json["hits"]["hits"][0]
    data["metadata"]["title"] = "New title"
    data["metadata"]["some_bool_val"] = False

    # Update it
    res = client.put(f"/draft-test/{id_}/draft", headers=headers.json, data=json.dumps(data))
    assert res.status_code == 200
    assert res.json["metadata"]["title"] == "New title"
    assert not res.json["metadata"]["some_bool_val"]

    # Check for UI representation on updated draft
    res = client.get(f"/draft-test/{id_}/draft", headers=headers.ui)
    assert res.status_code == 200
    assert set(res.json["ui"].keys()) == {
        "created_date_l10n_short",
        "created_date_l10n_medium",
        "created_date_l10n_long",
        "created_date_l10n_full",
        "updated_date_l10n_short",
        "updated_date_l10n_medium",
        "updated_date_l10n_long",
        "updated_date_l10n_full",
        "some_bool_val_i18n",
        "height",
        "is_draft",
    }
    assert res.json["ui"]["some_bool_val_i18n"] == "false"
    assert res.json["ui"]["height"] == "123"

    # Delete it
    res = client.delete(f"/draft-test/{id_}/draft")
    assert res.status_code == 204
    assert res.get_data(as_text=True) == ""

    Draft.index.refresh()

    # Try to get it again
    res = client.get(f"/draft-test/{id_}/draft", headers=headers.json)
    assert res.status_code == 404

    # Try to get search it again
    res = client.get("/user/draft-test", query_string={"q": f"id:{id_}"}, headers=headers.json)
    assert res.status_code == 200
    assert res.json["hits"]["total"] == 0


def add_file_to_draft(draft_file_service, draft_id, file_id, identity):
    """Add a file to the record."""
    result = draft_file_service.init_files(identity, draft_id, data=[{"key": file_id}])
    file_md = next(iter(result.entries))
    assert file_md["key"] == "test.txt"
    assert file_md["status"] == "pending"

    draft_file_service.set_file_content(
        identity,
        draft_id,
        file_id,
        BytesIO(b"test file content"),
    )
    result = draft_file_service.commit_file(identity, draft_id, file_id)
    file_md = result.data
    assert file_md["status"] == "completed"
    return result


def test_simple_flow_with_files(
    app,
    draft_service_with_files,
    draft_file_service,
    identity_simple,
    input_data,
    draft_model,
    search,
    search_clear,
    location,
):
    Record = draft_model.Record
    Draft = draft_model.Draft

    # Create an item
    item = draft_service_with_files.create(identity_simple, input_data)
    id_ = item.id
    Draft.index.refresh()

    # Add a file
    add_file_to_draft(draft_file_service, id_, "test.txt", identity_simple)

    # Can not publish as publishing needs files support in drafts
    assert draft_service_with_files.publish(identity_simple, id_)

    draft_service_with_files.delete(identity_simple, id_)
    Record.index.refresh()

    # Retrieve it - deleted so cannot
    # - db
    pytest.raises(PIDDeletedError, draft_service_with_files.read, identity_simple, id_)
    # - search
    res = draft_service_with_files.search(
        identity_simple,
        q=f"id:{id_}",
        size=25,
        page=1,
    )
    assert res.total == 0
