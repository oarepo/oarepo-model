#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for record exports."""

from __future__ import annotations


def test_exports(
    app,
    input_data_more_complex,
    empty_model,
    search_clear,
    location,
    client,
    headers,
):
    assert {x.code for x in empty_model.exports} == {
        "json",
        "lset",
        "jsonlset",
        "ui_json",
    }

    assert empty_model.RecordResourceConfig().response_handlers.keys() == {
        "application/json",
        "application/linkset",
        "application/linkset+json",
        "application/vnd.inveniordm.v1+json",
    }
