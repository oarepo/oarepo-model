# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Fields searched by a full-text query: ``SetDefaultSearchFields``.

Sets the fields that a plain query (``?q=microscope``, without a field name) is
matched against.

Every field must be a text field - ``keyword``, ``fulltext`` or ``fulltext+keyword``
(or a text sub-field). Any other type makes searches fail with ``failed to create
query: For input string: "..."``. To search a number, add a ``keyword`` sub-field
with ``PatchIndexPropertyMapping`` and list that sub-field here.

Example (in ``model.py``):

```python
from oarepo_model.customizations import (
    SetDefaultSearchFields,
)

SetDefaultSearchFields(
    "metadata.title",
    "metadata.description",
)
```

See https://nrp-cz.github.io/docs/customize/model_backend/search#available-search-customizations
"""

from __future__ import annotations

from .index_settings import PatchIndexSettings


class SetDefaultSearchFields(PatchIndexSettings):
    """Customization to specify a set of search fields."""

    modifies = ("record-mapping",)

    def __init__(self, *search_fields: str):
        """Initialize the customization with search fields to add."""
        super().__init__({"index.query.default_field": list(search_fields)})
