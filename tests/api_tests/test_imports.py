#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for record imports."""

from __future__ import annotations


def test_imports(
    app,
    input_data_more_complex,
    empty_model,
    csv_row_of_input_data_more_complex,
    csv_imports_model,
    search_clear,
    location,
    client,
    headers,
):
    assert {x.code for x in empty_model.imports} == {"json"}

    assert empty_model.RecordResourceConfig().request_body_parsers.keys() == {
        "application/json",
    }

    assert any(imp.mimetype == "text/csv" for imp in csv_imports_model.imports), (
        f"Registered imports: {[(i.code, i.mimetype) for i in csv_imports_model.imports]}"
    )

    res = client.post("csv-imports-test", headers=headers.csv, data=csv_row_of_input_data_more_complex)

    assert res.status_code == 201, res.get_data(as_text=True)

    assert res.json["metadata"] == input_data_more_complex["metadata"]
