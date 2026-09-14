# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Resource-level coverage for the media-file routes (P1-18) and draft upload gate (P1-12).

Media files live at a distinct '/media-files' URL, not the plain '/files' one that draft/
published records already use, and a draft's media files must be uploadable even though a
published record's media files stay read-only.
"""

from __future__ import annotations

import json


def test_simple_flow_media_files_resource(
    app,
    client,
    identity_simple,
    draft_model_with_files,
    search,
    search_clear,
    location,
    headers,
    input_data,
):
    # Create a draft with both plain and media files enabled
    input_data["media_files"] = {"enabled": True}
    res = client.post("/draft-with-files", headers=headers.json, data=json.dumps(input_data))
    assert res.status_code == 201
    id_ = res.json["id"]

    # A plain file and a media file are independent entries, not aliases of the same route
    res = client.post(
        f"/draft-with-files/{id_}/draft/files",
        headers=headers.json,
        data=json.dumps([{"key": "plain.txt"}]),
    )
    assert res.status_code == 201

    res = client.post(
        f"/draft-with-files/{id_}/draft/media-files",
        headers=headers.json,
        data=json.dumps([{"key": "media.bin"}]),
    )
    assert res.status_code == 201

    res = client.get(f"/draft-with-files/{id_}/draft/files", headers=headers.json)
    assert {entry["key"] for entry in res.json["entries"]} == {"plain.txt"}

    res = client.get(f"/draft-with-files/{id_}/draft/media-files", headers=headers.json)
    assert {entry["key"] for entry in res.json["entries"]} == {"media.bin"}

    # A draft's media file content must be uploadable and committable
    res = client.put(
        f"/draft-with-files/{id_}/draft/media-files/media.bin/content",
        data=b"media content",
        content_type="application/octet-stream",
    )
    assert res.status_code == 200

    res = client.post(f"/draft-with-files/{id_}/draft/media-files/media.bin/commit")
    assert res.status_code == 200
    assert res.json["status"] == "completed"

    res = client.get(f"/draft-with-files/{id_}/draft/media-files/media.bin/content")
    assert res.status_code == 200
    assert res.get_data() == b"media content"

    # Publishing needs the plain file committed too
    res = client.put(
        f"/draft-with-files/{id_}/draft/files/plain.txt/content",
        data=b"plain content",
        content_type="application/octet-stream",
    )
    assert res.status_code == 200
    res = client.post(f"/draft-with-files/{id_}/draft/files/plain.txt/commit")
    assert res.status_code == 200

    records_service = app.extensions["draft_with_files"].records_service
    records_service.publish(identity_simple, id_)

    # A published record's media files stay read-only: uploading must not be possible
    res = client.post(
        f"/draft-with-files/{id_}/media-files",
        headers=headers.json,
        data=json.dumps([{"key": "other.bin"}]),
    )
    assert res.status_code == 405

    # ... but its (already committed) media file content is still readable
    res = client.get(f"/draft-with-files/{id_}/media-files/media.bin/content")
    assert res.status_code == 200
    assert res.get_data() == b"media content"
