#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for feature presets."""

from __future__ import annotations

from packaging.version import Version


def test_records_cf_model_features(
    app,
    identity_simple,
    records_cf_model,
    input_data,
    search,
):
    # check versions of features using invenio-records-resources
    assert Version(app.extensions["oarepo-runtime"].models["records_cf"].features["records"]["version"]) >= Version(
        "8.6.0.post1001"
    )
    assert Version(app.extensions["records_cf"].model_arguments["features"]["records"]["version"]) >= Version(
        "8.6.0.post1001"
    )

    assert Version(app.extensions["oarepo-runtime"].models["records_cf"].features["files"]["version"]) >= Version(
        "8.6.0.post1001"
    )
    assert Version(app.extensions["records_cf"].model_arguments["features"]["files"]["version"]) >= Version(
        "8.6.0.post1001"
    )

    assert Version(
        app.extensions["oarepo-runtime"].models["records_cf"].features["custom-fields"]["version"]
    ) >= Version("8.6.0.post1001")
    assert Version(app.extensions["records_cf"].model_arguments["features"]["custom-fields"]["version"]) >= Version(
        "8.6.0.post1001"
    )


def test_relation_model_features(
    app,
    identity_simple,
    relation_model,
    input_data,
    search,
):
    # check versions of features using invenio-records-resources
    assert Version(app.extensions["oarepo-runtime"].models["relation_test"].features["records"]["version"]) >= Version(
        "8.6.0.post1001"
    )
    assert Version(app.extensions["relation_test"].model_arguments["features"]["records"]["version"]) >= Version(
        "8.6.0.post1001"
    )

    assert Version(app.extensions["oarepo-runtime"].models["relation_test"].features["files"]["version"]) >= Version(
        "8.6.0.post1001"
    )
    assert Version(app.extensions["relation_test"].model_arguments["features"]["files"]["version"]) >= Version(
        "8.6.0.post1001"
    )

    assert Version(
        app.extensions["oarepo-runtime"].models["relation_test"].features["relations"]["version"]
    ) >= Version("8.6.0.post1001")
    assert Version(app.extensions["relation_test"].model_arguments["features"]["relations"]["version"]) >= Version(
        "8.6.0.post1001"
    )


def test_ui_links_model_features(
    app,
    identity_simple,
    ui_links_model,
    input_data,
    search,
):
    # check versions of features using invenio-records-resources
    assert Version(app.extensions["oarepo-runtime"].models["test_ui_links"].features["records"]["version"]) >= Version(
        "8.6.0.post1001"
    )
    assert Version(app.extensions["test_ui_links"].model_arguments["features"]["records"]["version"]) >= Version(
        "8.6.0.post1001"
    )

    assert Version(app.extensions["oarepo-runtime"].models["test_ui_links"].features["ui"]["version"]) >= Version(
        "8.6.0.post1001"
    )
    assert Version(app.extensions["test_ui_links"].model_arguments["features"]["ui"]["version"]) >= Version(
        "8.6.0.post1001"
    )

    # check versions of features using invenio-drafts-resources
    assert Version(
        app.extensions["oarepo-runtime"].models["test_ui_links"].features["drafts-records"]["version"]
    ) >= Version("7.2.0.post1001")
    assert Version(app.extensions["test_ui_links"].model_arguments["features"]["drafts-records"]["version"]) >= Version(
        "7.2.0.post1001"
    )

    # check unknown version of oarepo-ui package
    assert app.extensions["oarepo-runtime"].models["test_ui_links"].features["ui-links"]["version"] == "unknown"
    assert app.extensions["test_ui_links"].model_arguments["features"]["ui-links"]["version"] == "unknown"
