# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from unittest.mock import MagicMock

from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations import AddEntryPoint


def _builder():
    model = MagicMock(base_name="record")
    return model, InvenioModelBuilder(model, MagicMock())


def test_add_entry_point():
    model, builder = _builder()

    AddEntryPoint("invenio_base.api_blueprints", "records", "records_blueprint").apply(builder, model)

    assert builder.entry_points == {
        ("invenio_base.api_blueprints", "records"): "runtime_models_record:records_blueprint",
    }


def test_remove_entry_point():
    model, builder = _builder()

    AddEntryPoint("invenio_base.api_blueprints", "records", "records_blueprint").apply(builder, model)
    AddEntryPoint("invenio_base.api_blueprints", "records", None).apply(builder, model)

    assert builder.entry_points == {}
