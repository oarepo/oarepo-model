# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Computed ("synthetic") metadata fields.

A synthetic field is computed from the stored metadata when code reads it as
``record.metadata["<name>"]``. It is not stored in the database, and it is not part of
the iterated or serialized metadata, so it does not appear in API responses. A stored
value with the same name always takes precedence.

Example (in ``model.py``):

```python
from oarepo_model.customizations import (
    SetSyntheticMetadata,
)

SetSyntheticMetadata(
    display_name=lambda md: (
        f"{md.get('manufacturer', '')} {md.get('serial_number', '')}".strip()
    ),
)
```

See https://nrp-cz.github.io/docs/customize/model_backend/customizations#synthetic-metadata
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from ..base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class SetSyntheticMetadata(Customization):
    """Customization to add synthetic metadata to the model."""

    modifies = ("synthetic_metadata",)

    def __init__(self, **set_fns: Any):
        """Initialize the synthetic_metadata customization."""
        super().__init__("synthetic_metadata")
        self._set_fns = set_fns

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        s = builder.get_dictionary("synthetic_metadata")
        for key, value in self._set_fns.items():
            s[key] = value
