#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""High-level customization for setting models' permission policy.

This module provides the SetPermissionPolicy customization that sets the permission policy
for a given model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ..base import Customization

if TYPE_CHECKING:
    from invenio_records_permissions.policies.records import RecordPermissionPolicy

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class SetPermissionPolicy(Customization):
    """Customization to set model's permission policy."""

    modifies = ("PermissionPolicy",)

    def __init__(self, permission_policy: type[RecordPermissionPolicy], keep_mixins: bool = False):
        """Initialize the SetPermissionPolicy customization."""
        super().__init__("SetPermissionPolicy")
        self._permission_policy = permission_policy
        self._keep_mixins = keep_mixins

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        policy = builder.get_class("PermissionPolicy")
        policy.base_classes = [self._permission_policy]
        if not self._keep_mixins:
            policy.mixins = []
