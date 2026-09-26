# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

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
