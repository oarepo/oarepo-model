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


def test_search_items_use_full_links():
    """When the flag is True, links_search_item delegates to links_item."""
    from oarepo_model.customizations import PrependMixin
    from oarepo_model.model import ModelMixin
    from oarepo_model.presets.drafts import drafts_records_preset
    from oarepo_model.presets.records_resources import records_preset

    class UseFullLinks(ModelMixin):
        search_items_use_full_links = True

    m_on = model(
        name="test_full_links_on",
        version="1.0.0",
        presets=[records_preset, drafts_records_preset],
        customizations=[PrependMixin("RecordServiceConfig", UseFullLinks)],
    )
    config_on = m_on.RecordServiceConfig()
    assert config_on.search_items_use_full_links is True
    assert config_on.links_search_item == config_on.links_item

    m_default = model(
        name="test_full_links_default",
        version="1.0.0",
        presets=[records_preset, drafts_records_preset],
    )
    config_default = m_default.RecordServiceConfig()
    assert config_default.search_items_use_full_links is False
    assert config_default.links_search_item != config_default.links_item
