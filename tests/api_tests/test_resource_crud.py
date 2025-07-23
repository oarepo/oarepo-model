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


def test_simple_flow(
    app,
    input_data_more_complex,
    empty_model,
    search_clear,
    location,
    client,
    headers,
):
    """Test a simple REST API flow."""
    Record = empty_model.Record

    # Create a record
    res = client.post("/test", headers=headers.json, data=json.dumps(input_data_more_complex))
    assert res.status_code == 201
    id_ = res.json["id"]
    assert res.json["metadata"] == input_data_more_complex["metadata"]

    # Read the record
    res = client.get(f"/test/{id_}", headers=headers.json)
    assert res.status_code == 200
    assert res.json["metadata"] == input_data_more_complex["metadata"]

    res = client.get(f"/test/{id_}", headers=headers.ui)
    assert res.status_code == 200
    assert res.json["ui"].keys() == {
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
    }
    assert res.json["ui"]["some_bool_val_i18n"] == "true"
    assert res.json["ui"]["height"] == "123"

    Record.index.refresh()

    # Search it
    res = client.get("/test", query_string={"q": f"id:{id_}"}, headers=headers.json)
    assert res.status_code == 200
    assert res.json["hits"]["total"] == 1
    assert res.json["hits"]["hits"][0]["metadata"] == input_data_more_complex["metadata"]
    data = res.json["hits"]["hits"][0]
    data["metadata"]["title"] = "New title"
    data["metadata"]["some_bool_val"] = False

    # Update it
    res = client.put(f"/test/{id_}", headers=headers.json, data=json.dumps(data))
    assert res.status_code == 200
    assert res.json["metadata"]["title"] == "New title"
    assert not res.json["metadata"]["some_bool_val"]

    res = client.get(f"/test/{id_}", headers=headers.ui)
    assert res.status_code == 200
    assert res.json["ui"].keys() == {
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
    }
    assert res.json["ui"]["some_bool_val_i18n"] == "false"
    assert res.json["ui"]["height"] == "123"

    # Delete it
    res = client.delete(f"/test/{id_}")
    assert res.status_code == 204
    assert res.get_data(as_text=True) == ""

    Record.index.refresh()

    # Try to get it again
    res = client.get(f"/test/{id_}", headers=headers.json)
    assert res.status_code == 410

    # Try to get search it again
    res = client.get("/test", query_string={"q": f"id:{id_}"}, headers=headers.json)
    assert res.status_code == 200
    assert res.json["hits"]["total"] == 0
