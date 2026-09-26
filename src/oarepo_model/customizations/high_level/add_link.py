# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""High-level customization for adding item link to service config."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ..base import Customization

if TYPE_CHECKING:
    from invenio_records_resources.services import (
        ConditionalLink,
        EndpointLink,
        ExternalLink,
    )

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddLink(Customization):
    """Customization to add item link to record service config."""

    modifies = ("record_links_item",)

    def __init__(self, name: str, link: ExternalLink | EndpointLink | ConditionalLink):
        """Initialize the AddLink customization."""
        super().__init__(name)
        self._name = name
        self._link = link

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        links = builder.get_dictionary("record_links_item")
        links[self._name] = self._link
