#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for generated UI links."""

from __future__ import annotations

import json

import pytest
from flask import Blueprint


@pytest.fixture(scope="module")
def app_with_bp(app):
    bp = Blueprint("test_ui_links_ui", __name__)

    # mock UI resource
    @bp.route("/test-ui-links/preview/<pid_value>", methods=["GET"])
    def preview(pid_value: str) -> str:
        return "preview ok"

    @bp.route("/test-ui-links/", methods=["GET"])
    def search() -> str:
        return "search ok"

    @bp.route("/test-ui-links/uploads/<pid_value>", methods=["GET"])
    def deposit_edit(pid_value: str) -> str:
        return "deposit edit ok"

    @bp.route("/test-ui-links/uploads/new", methods=["GET"])
    def deposit_create() -> str:
        return "deposit create ok"

    @bp.route("/test-ui-links/records/<pid_value>")
    def record_detail(pid_value) -> str:
        return "detail ok"

    @bp.route("/test-ui-links/records/<pid_value>/latest", methods=["GET"])
    def record_latest(pid_value: str) -> str:
        return "latest ok"

    @bp.route("/test-ui-links/records/<pid_value>/export/<export_format>", methods=["GET"])
    def export(pid_value, export_format: str) -> str:
        return "export ok"

    app.register_blueprint(bp)
    return app


def test_ui_links(
    app_with_bp,
    identity_simple,
    ui_links_model,
    search,
    search_clear,
    location,
    client,
    headers,
):
    # Create a draft
    test_data = {"metadata": {"title": "test_title"}}

    res = client.post("/test-ui-links", headers=headers.json, data=json.dumps(test_data))
    assert res.status_code == 201
    assert "self_html" in res.json["links"]
    assert "latest_html" in res.json["links"]
    assert "preview_html" in res.json["links"]

    res = client.get("/test-ui-links")
    assert res.status_code == 200
    assert "self_html" in res.json["links"]

    res = client.get("/user/test-ui-links")
    assert res.status_code == 200
    assert "self_html" not in res.json["links"]  # not ready in oarep-ui yet
