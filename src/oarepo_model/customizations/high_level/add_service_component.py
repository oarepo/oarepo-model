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
    from invenio_records_resources.services.records.components import ServiceComponent

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddServiceComponent(Customization):
    """Customization to set model's permission policy."""

    modifies = ("record_service_components",)

    def __init__(self, component_cls: type[ServiceComponent]):
        """Initialize the AddServiceComponent customization."""
        super().__init__("AddServiceComponent")
        self._component_cls = component_cls

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        components = builder.get_list("record_service_components")
        components.append(self._component_cls)
