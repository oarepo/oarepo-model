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

import pytest
from flask import Blueprint
from oarepo_runtime import current_runtime


@pytest.fixture(scope="module")
def app_with_bp(app):
    bp = Blueprint("datacite_export_test_ui", __name__)

    # mock UI resource
    @bp.route("/preview/<pid_value>", methods=["GET"])
    def preview(pid_value: str) -> str:
        return "preview ok"

    @bp.route("/", methods=["GET"])
    def search() -> str:
        return "search ok"

    @bp.route("/uploads/<pid_value>", methods=["GET"])
    def deposit_edit(pid_value: str) -> str:
        return "deposit edit ok"

    @bp.route("/uploads/new", methods=["GET"])
    def deposit_create() -> str:
        return "deposit create ok"

    @bp.route("/records/<pid_value>")
    def record_detail(pid_value) -> str:
        return "detail ok"

    @bp.route("/records/<pid_value>/latest", methods=["GET"])
    def record_latest(pid_value: str) -> str:
        return "latest ok"

    @bp.route("/records/<pid_value>/export/<export_format>", methods=["GET"])
    def record_export(pid_value, export_format: str) -> str:
        return "export ok"

    app.register_blueprint(bp)
    return app


def test_signposting_linksets(
    app_with_bp,
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
    record_id = item.id
    assert linkset_export.serializer.serialize_object(item.to_dict()) == (
        f'<https://orcid.org/0000-0001-5727-2427>; rel=author; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://ror.org/04wxnsj81>; rel=author; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://doi.org/10.82433/b09z-4k37>; rel=cite-as; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://spdx.org/licenses/cc-by-4.0>; rel=license; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://schema.org/Dataset>; rel=type; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://schema.org/AboutPage>; rel=type; anchor="https://127.0.0.1:5000/uploads/{record_id}"'
    )
    assert json_linkset_export.serializer.serialize_object(item.to_dict()) == {
        "linkset": [
            {
                "anchor": f"https://127.0.0.1:5000/uploads/{record_id}",
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
    assert linkset_export.serializer.serialize_object(item.to_dict()) == ""
    assert json_linkset_export.serializer.serialize_object(item.to_dict()) == {}
