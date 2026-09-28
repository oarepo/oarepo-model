# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Service component: ``AddServiceComponent``.

Adds a component to the record service. A component is a subclass of
``invenio_records_resources.services.records.components.ServiceComponent`` whose
methods (``create``, ``update``, ``publish``, ``delete``, ...) run during the
corresponding service operations.

Example (in ``model.py``):

```python
from invenio_records_resources.services.records.components import (
    ServiceComponent,
)
from oarepo_model.customizations import (
    AddServiceComponent,
)


class NormalizeSerialComponent(
    ServiceComponent
):
    def create(
        self,
        identity,
        data=None,
        record=None,
        **kwargs,
    ):
        serial = record.metadata.get(
            "serial_number"
        )
        if serial:
            record.metadata[
                "serial_number"
            ] = serial.strip().upper()


AddServiceComponent(
    NormalizeSerialComponent
)
```

See https://nrp-cz.github.io/docs/customize/model_backend/customizations#service-components
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
