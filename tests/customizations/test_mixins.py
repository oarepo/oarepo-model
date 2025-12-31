#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import marshmallow as ma

from oarepo_model.api import model
from oarepo_model.customizations import (
    PrependMixin,
)
from oarepo_model.presets.records_resources import records_resources_preset


def test_metadata_add_mixin(model_types):
    class TestMixin:
        height = ma.fields.Float()

    m = model(
        name="metadata_mixin_test",
        version="1.0.0",
        presets=[
            records_resources_preset,
        ],
        types=[model_types],
        customizations=[
            PrependMixin("MetadataSchema", TestMixin),
        ],
        metadata_type="Metadata",
    )
    metadata_schema_cls = m.RecordSchema().fields["metadata"].nested()
    assert issubclass(metadata_schema_cls, TestMixin)
    assert isinstance(metadata_schema_cls().fields["height"], ma.fields.Float)
