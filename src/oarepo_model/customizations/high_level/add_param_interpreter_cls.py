# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Custom search parameter: ``AddParamInterpreterCls``.

Adds a search parameter interpreter (a subclass of
``invenio_records_resources.services.records.params.base.ParamInterpreter``) that
changes the search query based on URL query-string parameters. Extra interpreters
run before the facets interpreter, so they can take their own parameters out of
``params`` before those are treated as facet filters. The ``geo_*`` and ``icrs_*``
search parameters are implemented this way.

Example (in ``model.py``):

```python
from invenio_records_resources.services.records.params.base import (
    ParamInterpreter,
)
from oarepo_model.customizations import (
    AddParamInterpreterCls,
)


class OnlyWithFilesParam(
    ParamInterpreter
):
    def apply(
        self, identity, search, params
    ):
        facets = params.get(
            "facets", {}
        )
        value = params.pop(
            "with_files", None
        ) or facets.pop(
            "with_files", None
        )
        if value and value[0] == "true":
            search = search.filter(
                "term",
                **{
                    "files.enabled": True
                },
            )
        return search


AddParamInterpreterCls(
    OnlyWithFilesParam
)
```

See https://nrp-cz.github.io/docs/customize/model_backend/search#custom-search-parameters-
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..add_to_list import AddToList

if TYPE_CHECKING:
    from invenio_records_resources.services.records.params.base import ParamInterpreter


class AddParamInterpreterCls(AddToList):
    """Customization to add an extra search parameter interpreter class to the model."""

    def __init__(self, clazz: type[ParamInterpreter]):
        """Initialize the AddParamInterpreterCls customization."""
        super().__init__("extra_param_interpreter_classes", clazz)
