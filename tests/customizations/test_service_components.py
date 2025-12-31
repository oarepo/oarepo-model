#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from invenio_records_resources.services.records.components import ServiceComponent

from oarepo_model.api import model
from oarepo_model.customizations import (
    AddServiceComponent,
)
from oarepo_model.presets.records_resources import records_resources_preset


class TestServiceComponent(ServiceComponent):
    """Test service component."""


def test_add_service_component():
    m = model(
        name="test_add_service_component",
        version="1.0.0",
        presets=[
            records_resources_preset,
        ],
        customizations=[
            AddServiceComponent(TestServiceComponent),
        ],
    )

    # ideally check whether the component actually ends in the service components list after app init
    assert len([c for c in m.record_service_components if issubclass(c, TestServiceComponent)]) == 1
