#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from oarepo_model.presets.records_resources.records.synthetic_metadata import (
    MetadataProxy,
)


def test_record_metadata_field_uses_synthetic_dictionary(
    app,
    synthetic_metadata_service,
    synthetic_metadata_model,
    identity_simple,
    search_clear,
    location,
):
    Record = synthetic_metadata_model.Record

    item = synthetic_metadata_service.create(
        identity_simple,
        {"metadata": {"title": "hello"}, "files": {"enabled": True}},
    )

    record = Record.pid.resolve(item.id)

    assert isinstance(record.metadata, MetadataProxy)
    assert record.metadata["title"] == "hello"
    assert record.metadata["title_upper"] == "HELLO"
