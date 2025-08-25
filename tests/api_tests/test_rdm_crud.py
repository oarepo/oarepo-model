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
    file_md = list(result.entries)
    assert any(file["status"] == "pending" and file["key"] == file_id for file in file_md)

    service.set_file_content(identity, draft_id, file_id, BytesIO(b"test file content"))
    result = service.commit_file(identity, draft_id, file_id)
    file_md = result.data
    assert file_md["status"] == "completed"
    return result


def add_image_to_draft(service, draft_id, file_id, identity):
    """Add a file to the record."""
    result = service.init_files(identity, draft_id, data=[{"key": file_id}])
    file_md = list(result.entries)
    assert any(file["status"] == "pending" and file["key"] == "test_image.jpg" for file in file_md)

    with open("tests/test-pic.jpg", "rb") as f:
        service.set_file_content(identity, draft_id, file_id, f)

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


def test_rdm_links(
    app,
    test_rdm_service,
    test_rdm_draft_files_service,
    test_rdm_draft_media_files_service,
    identity_simple,
    input_data,
    client,
    rdm_model,
    search,
    search_clear,
    headers,
    location,
):
    input_data["media_files"] = {"enabled": True}

    # input_data["pids"] = {"doi": {"client": "datacite", "identifier": "10.81088/jxt9h-ap045", "provider": "datacite"}}

    Record = rdm_model.Record
    Draft = rdm_model.Draft

    # Create an item
    item = test_rdm_service.create(identity_simple, input_data)
    id_ = item.id
    Draft.index.refresh()

    # Add a file
    res = add_file_to_draft(test_rdm_draft_files_service, id_, "test.txt", identity_simple)
    res = add_image_to_draft(test_rdm_draft_files_service, id_, "test_image.jpg", identity_simple)

    res = add_file_to_draft(test_rdm_draft_media_files_service, id_, "test", identity_simple)
    res = add_file_to_draft(test_rdm_draft_media_files_service, id_, "test2", identity_simple)

    # Can not publish as publishing needs files support in drafts
    res = test_rdm_service.publish(identity_simple, id_)
    id__ = res["id"]

    ret = client.get(f"/rdm-test/{id__}")
    assert ret.status_code == 200
    links = ret.json["links"]

    parent_link = links.pop("parent")
    parent_link = parent_link.replace("https://127.0.0.1:5000/api", "")
    ret = client.get(parent_link)
    assert ret.status_code == 302

    # TODO: uncomment to test DOI links as soon as oarepo-doi will be rdm13 compatible
    # doi_link = links.pop("doi")
    # assert doi_link == "https://doi.org/10.81088/jxt9h-ap045"

    # self_doi_link = links.pop("self_doi")
    # assert self_doi_link == "https://doi.org/10.81088/jxt9h-ap045"

    # self_doi_html_link = links.pop("self_doi_html")
    # assert self_doi_html_link == "https://127.0.0.1:5000/doi/10.81088/jxt9h-ap045"

    # parent_doi_link = links.pop("parent_doi")
    # assert parent_doi_link == "https://doi.org/10.81088/jxt9h-ap045"

    # parent_doi_html_link = links.pop("parent_doi_html")
    # assert parent_doi_html_link == "https://127.0.0.1:5000/doi/10.81088/jxt9h-ap045"

    self_iiif_manifest_link = links.pop("self_iiif_manifest")
    # in the link there should go to the /api endpoint first after ip adress
    assert self_iiif_manifest_link == f"https://127.0.0.1:5000/iiif/record:{id__}/manifest"

    self_iiif_sequence_link = links.pop("self_iiif_sequence")
    # in the link there should go to the /api endpoint first after ip adress
    assert self_iiif_sequence_link == f"https://127.0.0.1:5000/iiif/record:{id__}/sequence/default"

    files_link = links.pop("files")
    files_link = files_link.replace("https://127.0.0.1:5000/api", "")
    ret = client.get(files_link)
    assert ret.status_code == 200
    assert len(ret.json["entries"]) == 2  # 2 uploaded files
    assert ret.json["entries"][0]["key"] == "test.txt"  # correct name
    assert ret.json["entries"][1]["key"] == "test_image.jpg"  # correct name

    media_files_link = links.pop("media_files")
    media_files_link = media_files_link.replace("https://127.0.0.1:5000/api", "")
    ret = client.get(media_files_link)
    assert ret.status_code == 200

    thumbnails_links = links.pop("thumbnails")
    assert len(thumbnails_links) == 1  # 500x500 as defined in conftest
    assert (
        thumbnails_links["500"]
        == f"https://127.0.0.1:5000/iiif/record:{id__}:test_image.jpg/full/%5E500,/0/default.jpg"
    )

    archive_link = links.pop("archive")
    archive_link = archive_link.replace("https://127.0.0.1:5000/api", "")
    ret = client.get(archive_link)
    assert ret.status_code == 200
    assert "application/zip" in ret.headers["Content-Type"]

    archive_media_files = links.pop("archive_media")
    archive_media_files = archive_media_files.replace("https://127.0.0.1:5000/api", "")
    ret = client.get(archive_media_files)
    assert ret.status_code == 200

    access_links = links.pop("access_links")
    access_links = access_links.replace("https://127.0.0.1:5000/api", "")
    # ret = client.get(access_links)
    # assert ret.status_code == 200

    access_grants = links.pop("access_grants")
    access_grants = access_grants.replace("https://127.0.0.1:5000/api", "")
    # ret = client.get(access_grants)
    # assert ret.status_code == 200

    access_users_link = links.pop("access_users")
    access_users_link = access_users_link.replace("https://127.0.0.1:5000/api", "")
    # ret = client.get(access_users_link)
    # assert ret.status_code == 200

    access_group_link = links.pop("access_groups")
    access_group_link = access_group_link.replace("https://127.0.0.1:5000/api", "")
    # ret = client.get(access_group_link)
    # assert ret.status_code == 200

    # Links for access_request and access are there but not working for now
    access_request = links.pop("access_request")
    access_request = access_request.replace("https://127.0.0.1:5000/api", "")
    # ret = client.get(access_request)
    # assert ret.status_code == 200

    access = links.pop("access")
    access = access.replace("https://127.0.0.1:5000/api", "")
    # ret = client.get(access)
    # assert ret.status_code == 200
