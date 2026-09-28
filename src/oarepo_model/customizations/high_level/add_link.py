# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Record link: ``AddLink``.

Adds an entry to the ``links`` of every record in API responses. The link is one of
the link classes of ``invenio_records_resources.services`` (``ExternalLink``,
``EndpointLink``, ``ConditionalLink``, ...).

Import it from this module - unlike the other customizations, it is not exported
from ``oarepo_model.customizations``.

Example (in ``model.py``):

```python
from invenio_records_resources.services import (
    ExternalLink,
)
from oarepo_model.customizations.high_level import (
    AddLink,
)

AddLink(
    "manufacturer_catalogue",
    ExternalLink(
        "https://catalogue.example.org/{serial}",
        vars=lambda record, vars: (
            vars.update(
                {
                    "serial": record.metadata.get(
                        "serial_number",
                        "",
                    )
                }
            )
        ),
    ),
)
```

See https://nrp-cz.github.io/docs/customize/model_backend/customizations#links
"""

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
