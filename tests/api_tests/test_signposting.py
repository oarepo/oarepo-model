#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for record signposting exports."""

from __future__ import annotations

from oarepo_runtime import current_runtime


def test_signposting_linksets(
    app,
    test_datacite_service,
    file_service,
    identity_simple,
    input_data,
    datacite_exports_model,
    search_clear,
    location,
    client,
    headers,
):
    item = test_datacite_service.create(identity_simple, input_data)

    assert {x.code for x in datacite_exports_model.exports} == {"json", "lset", "jsonlset", "ui_json", "datacite"}

    assert datacite_exports_model.RecordResourceConfig().response_handlers.keys() == {
        "application/json",
        "application/linkset",
        "application/linkset+json",
        "application/vnd.inveniordm.v1+json",
        "application/vnd.datacite.datacite+json",
    }
    linkset_export = current_runtime.models["datacite_export_test"].get_export_by_mimetype("application/linkset")
    json_linkset_export = current_runtime.models["datacite_export_test"].get_export_by_mimetype(
        "application/linkset+json"
    )
    assert linkset_export.serializer.serialize_object(item) == (
        ""
        f'<https://orcid.org/0000-0001-5727-2427>; rel=author; anchor="https://127.0.0.1:5000/uploads/{item.id}", '
        f'<https://ror.org/04wxnsj81>; rel=author; anchor="https://127.0.0.1:5000/uploads/{item.id}", '
        f'<https://doi.org/10.82433/b09z-4k37>; rel=cite-as; anchor="https://127.0.0.1:5000/uploads/{item.id}", '
        f'<https://spdx.org/licenses/cc-by-4.0>; rel=license; anchor="https://127.0.0.1:5000/uploads/{item.id}", '
        f'<https://schema.org/Dataset>; rel=type; anchor="https://127.0.0.1:5000/uploads/{item.id}", '
        f'<https://schema.org/AboutPage>; rel=type; anchor="https://127.0.0.1:5000/uploads/{item.id}"'
    )
    assert json_linkset_export.serializer.serialize_object(item) == {
        "linkset": [
            {
                "anchor": f"https://127.0.0.1:5000/uploads/{item.id}",
                "author": [{"href": "https://orcid.org/0000-0001-5727-2427"}, {"href": "https://ror.org/04wxnsj81"}],
                "cite-as": [{"href": "https://doi.org/10.82433/b09z-4k37"}],
                "license": [{"href": "https://spdx.org/licenses/cc-by-4.0"}],
                "type": [{"href": "https://schema.org/Dataset"}, {"href": "https://schema.org/AboutPage"}],
            }
        ]
    }


def test_signposting_linksets_without_datacite(
    app,
    test_service,
    file_service,
    identity_simple,
    input_data,
    empty_model,
    search_clear,
    location,
    client,
    headers,
):
    item = test_service.create(identity_simple, input_data)

    assert {x.code for x in empty_model.exports} == {"json", "lset", "jsonlset", "ui_json"}

    assert empty_model.RecordResourceConfig().response_handlers.keys() == {
        "application/json",
        "application/linkset",
        "application/linkset+json",
        "application/vnd.inveniordm.v1+json",
    }
    linkset_export = current_runtime.models["test"].get_export_by_mimetype("application/linkset")
    json_linkset_export = current_runtime.models["test"].get_export_by_mimetype("application/linkset+json")
    assert linkset_export.serializer.serialize_object(item) == ""
    assert json_linkset_export.serializer.serialize_object(item) == {}
