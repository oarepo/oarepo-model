# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Boolean data type: ``boolean``.

Only JSON ``true``/``false`` (and the numbers ``1``/``0``) are accepted; strings such
as ``"true"`` are rejected. The field gets a facet, and the UI serialization adds a
sibling ``<field>_i18n`` key with the localized "true"/"false" text (the value
itself is kept unchanged). In the UI, the field is typically rendered as a checkbox.

Example (model YAML):

```yaml
peer_reviewed:
  type: boolean
open_access:
  type: boolean
```

Search: ``peer_reviewed:true AND open_access:true``.

See https://nrp-cz.github.io/docs/customize/model_backend/model_reference#boolean
"""

from __future__ import annotations

from typing import Any, override

import marshmallow
from invenio_i18n import gettext

from .base import DataType, FacetMixin


class FormatBoolean(marshmallow.fields.Field):
    """Helper class for formatting single values of booleans."""

    @override
    def _serialize(self, value: Any, attr: str | None, obj: Any, **kwargs: Any) -> Any:
        if value is None:
            return None

        yes = gettext("true")
        no = gettext("false")
        return yes if value else no


class BooleanDataType(FacetMixin, DataType):
    """Data type for boolean values."""

    TYPE = "boolean"

    marshmallow_field_class = marshmallow.fields.Boolean
    jsonschema_type = "boolean"
    mapping_type = "boolean"

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a Marshmallow UI fields for Boolean value, specifically i18n format."""
        field_class = self._get_ui_marshmallow_field_class(field_name, element) or FormatBoolean
        return {
            f"{field_name}_i18n": field_class(attribute=field_name),
        }

    @override
    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
        ret["truthy"] = [True]
        ret["falsy"] = [False]
        return ret
