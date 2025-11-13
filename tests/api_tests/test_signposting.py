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
    linkset_export = (
        current_runtime.models["datacite_export_test"]
        .get_export_by_mimetype("application/linkset")
        .serializer.serialize_object(item.to_dict())
    )
    json_linkset_export = (
        current_runtime.models["datacite_export_test"]
        .get_export_by_mimetype("application/linkset+json")
        .serializer.serialize_object(item.to_dict())
    )
    record_id = item.id

    assert "<https://orcid.org/0000-0001-5727-2427>; rel=author" in linkset_export
    assert "<https://ror.org/04wxnsj81>; rel=author" in linkset_export
    assert "<https://doi.org/10.82433/b09z-4k37>; rel=cite-as" in linkset_export
    assert "<https://spdx.org/licenses/cc-by-4.0>; rel=license" in linkset_export
    assert "<https://schema.org/Dataset>; rel=type" in linkset_export
    assert "<https://schema.org/AboutPage>; rel=type" in linkset_export
    assert f'/uploads/{record_id}>; rel=describes; type="text/html"' in linkset_export
    assert f'/records/{record_id}/export/json>; rel=describedby; type="application/json"' in linkset_export
    assert f'/records/{record_id}/export/jsonlset>; rel=describedby; type="application/linkset+json"' in linkset_export
    assert f'/records/{record_id}/export/lset>; rel=describedby; type="application/linkset"' in linkset_export
    assert (
        f'/records/{record_id}/export/ui_json>; rel=describedby; type="application/vnd.inveniordm.v1+json"'
        in linkset_export
    )
    assert (
        f'/records/{record_id}/export/datacite>; rel=describedby; type="application/vnd.datacite.datacite+json"'
        in linkset_export
    )

    json_linkset_signposting_types = json_linkset_export["linkset"][0].keys()
    assert "anchor" in json_linkset_signposting_types
    assert "author" in json_linkset_signposting_types
    assert "cite-as" in json_linkset_signposting_types
    assert "describedby" in json_linkset_signposting_types
    assert "license" in json_linkset_signposting_types
    assert "type" in json_linkset_signposting_types


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
