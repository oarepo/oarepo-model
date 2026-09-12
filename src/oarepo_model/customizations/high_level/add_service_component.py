# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""High-level customization for adding service components to models.

This module provides the AddServiceComponent customization that appends
a service component class to the record service components list.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..add_to_list import AddToList

if TYPE_CHECKING:
    from invenio_records_resources.services.records.components import ServiceComponent


class AddServiceComponent(AddToList):
    """Customization to add a service component to the record service."""

    def __init__(self, component_cls: type[ServiceComponent]):
        """Initialize the AddServiceComponent customization."""
        super().__init__("record_service_components", component_cls)
