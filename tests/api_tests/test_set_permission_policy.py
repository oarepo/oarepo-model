#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from invenio_records_permissions.policies.records import RecordPermissionPolicy

from oarepo_model.api import model
from oarepo_model.customizations import PrependMixin, SetPermissionPolicy
from oarepo_model.presets.records_resources import records_resources_preset


class MyPermissionPolicy(RecordPermissionPolicy):
    """Dummy permission policy."""


class MyMixin:
    """Dummy mixin."""


def test_set_permission_policy(
    app,
    search_clear,
):
    m = model(
        name="test_permission_policy_without_mixins",
        version="1.0.0",
        presets=[
            records_resources_preset,
        ],
        customizations=[
            PrependMixin("PermissionPolicy", MyMixin),
            SetPermissionPolicy(MyPermissionPolicy),
        ],
    )

    assert issubclass(m.PermissionPolicy, MyPermissionPolicy)
    assert not issubclass(m.PermissionPolicy, MyMixin)

    m = model(
        name="test_permission_policy_with_mixins",
        version="1.0.0",
        presets=[
            records_resources_preset,
        ],
        customizations=[
            PrependMixin("PermissionPolicy", MyMixin),
            SetPermissionPolicy(MyPermissionPolicy, keep_mixins=True),
        ],
    )

    assert issubclass(m.PermissionPolicy, MyPermissionPolicy)
    assert issubclass(m.PermissionPolicy, MyMixin)
