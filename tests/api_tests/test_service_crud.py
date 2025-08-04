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
from invenio_pidstore.errors import PIDDeletedError


def test_simple_flow(
    app,
    test_service,
    file_service,
    identity_simple,
    input_data,
    empty_model,
    search,
    search_clear,
    location,
):
    Record = empty_model.Record

    # Create an item
    item = test_service.create(identity_simple, input_data)
    id_ = item.id

    # Read it
    read_item = test_service.read(identity_simple, id_)
    assert item.id == read_item.id
    assert item.data == read_item.data

    # Refresh to make changes live
    Record.index.refresh()

    # Search it
    res = test_service.search(identity_simple, q=f"id:{id_}", size=25, page=1)
    assert res.total == 1
    assert next(iter(res.hits)) == read_item.data

    # Scan it
    res = test_service.scan(identity_simple, q=f"id:{id_}")
    assert res.total is None
    assert next(iter(res.hits)) == read_item.data

    # Update it
    data = read_item.data
    data["metadata"]["title"] = "New title"
    update_item = test_service.update(identity_simple, id_, data)
    assert item.id == update_item.id
    assert update_item["metadata"]["title"] == "New title"

    # files part
    file_to_initialise = [
        {
            "key": "article.txt",
            "checksum": "md5:c785060c866796cc2a1708c997154c8e",
            "size": 17,  # 2kB
            "metadata": {
                "description": "Published article PDF.",
            },
        },
    ]
    # Initialize file saving
    result = file_service.init_files(identity_simple, id_, file_to_initialise)
    file_result = result.to_dict()["entries"][0]
    assert file_result["key"] == file_to_initialise[0]["key"]
    assert file_result["checksum"] == file_to_initialise[0]["checksum"]
    assert file_result["size"] == file_to_initialise[0]["size"]
    assert file_result["metadata"] == file_to_initialise[0]["metadata"]
    # for to_file in to_files:
    content = BytesIO(b"test file content")
    result = file_service.set_file_content(
        identity_simple,
        id_,
        file_to_initialise[0]["key"],
        content,
        content.getbuffer().nbytes,
    )
    # TODO: figure response for succesfully saved file
    assert result.to_dict()["key"] == file_to_initialise[0]["key"]

    result = file_service.commit_file(identity_simple, id_, "article.txt")
    # TODO: currently there is no status in the json between the initialisation
    # and the commiting.
    assert result.to_dict()["key"] == file_to_initialise[0]["key"]

    # List files
    result = file_service.list_files(identity_simple, id_)
    assert result.to_dict()["entries"][0]["key"] == file_to_initialise[0]["key"]
    assert result.to_dict()["entries"][0]["storage_class"] == "L"
    assert "uri" not in result.to_dict()["entries"][0]

    # Read file metadata
    result = file_service.read_file_metadata(identity_simple, id_, "article.txt")
    assert result.to_dict()["key"] == file_to_initialise[0]["key"]
    assert result.to_dict()["storage_class"] == "L"

    # Retrieve file
    result = file_service.get_file_content(identity_simple, id_, "article.txt")
    assert result.file_id == "article.txt"

    # Delete file
    result = file_service.delete_file(identity_simple, id_, "article.txt")
    assert result.file_id == "article.txt"

    # Assert deleted
    result = file_service.list_files(identity_simple, id_)
    assert result.entries
    assert len(list(result.entries)) == 0

    # Delete it
    assert test_service.delete(identity_simple, id_)

    # Refresh to make changes live
    Record.index.refresh()

    # Retrieve it - deleted so cannot
    # - db
    pytest.raises(PIDDeletedError, test_service.read, identity_simple, id_)
    # - search
    res = test_service.search(identity_simple, q=f"id:{id_}", size=25, page=1)
    assert res.total == 0
