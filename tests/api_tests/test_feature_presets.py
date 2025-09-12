#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations


def test_records_cf_model_features(
    app,
    identity_simple,
    records_cf_model,
    input_data,
    search,
):
    # get model features from oarepo-runtime extension
    assert app.extensions["oarepo-runtime"].models["records_cf"].features == {
        "records": {"version": "0.1.0dev8"},
        "files": {"version": "0.1.0dev8"},
        "custom-fields": {"version": "0.1.0dev8"},
    }

    # get model features from a model extension
    assert app.extensions["records_cf"].model_arguments["features"] == {
        "records": {"version": "0.1.0dev8"},
        "files": {"version": "0.1.0dev8"},
        "custom-fields": {"version": "0.1.0dev8"},
    }


def test_relation_model_features(
    app,
    identity_simple,
    relation_model,
    input_data,
    search,
):
    # get model features from oarepo-runtime extension
    assert app.extensions["oarepo-runtime"].models["records_cf"].features == {
        "records": {"version": "0.1.0dev8"},
        "files": {"version": "0.1.0dev8"},
        "custom-fields": {"version": "0.1.0dev8"},
    }

    # get model features from a model extension
    assert app.extensions["records_cf"].model_arguments["features"] == {
        "records": {"version": "0.1.0dev8"},
        "files": {"version": "0.1.0dev8"},
        "custom-fields": {"version": "0.1.0dev8"},
    }
