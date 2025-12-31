#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from invenio_records_resources.services import ExternalLink

from oarepo_model.api import model
from oarepo_model.customizations.high_level.add_link import AddLink
from oarepo_model.presets.records_resources import records_resources_preset


def test_add_link():
    tested_link = ExternalLink("/not/a/link")

    m = model(
        name="test_add_link",
        version="1.0.0",
        presets=[
            records_resources_preset,
        ],
        customizations=[
            AddLink("test_link", tested_link),
        ],
    )

    assert "test_link" in m.record_links_item
    assert m.record_links_item["test_link"] == tested_link
