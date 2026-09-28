# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Import format: ``AddMetadataImport``.

Registers a deserializer for creating and updating records from another format.
The REST API picks it by the ``Content-Type`` of the request; the deserializer
returns the record in the internal JSON structure, which is then validated as usual.
JSON (``application/json``) is always available. ``description`` is required; set
``oai_name`` to use the format for OAI-PMH harvesting.

Example (in ``model.py``):

```python
from invenio_i18n import (
    lazy_gettext as _,
)
from oarepo_model.customizations import (
    AddMetadataImport,
)

AddMetadataImport(
    code="csv",
    name=_("CSV"),
    mimetype="text/csv",
    deserializer=CSVDeserializer(),
    description=_(
        "A CSV file with one row"
    ),
)
```

See https://nrp-cz.github.io/docs/customize/model_backend/exports_and_imports#adding-custom-import-formats
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_runtime.api import Import

from ..base import Customization

if TYPE_CHECKING:
    from flask_babel.speaklater import LazyString
    from flask_resources.deserializers import DeserializerMixin

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddMetadataImport(Customization):
    """Customization to add metadata import to the model."""

    modifies = ("imports",)

    def __init__(  # noqa PLR0913 arguments needed in callback
        self,
        code: str,
        name: LazyString,
        mimetype: str,
        deserializer: DeserializerMixin,
        description: LazyString,
        oai_name: tuple[str, str] | None = None,
        **kwargs: Any,  # noqa ARG002 accepted for backwards compatibility, ignored (see P1-9)
    ):
        """Initialize the AddMetadataImport customization.

        :param code: Code of the import format, used to identify the import format in the URL.
        :param name: Name of the import format, human-readable.
        :param description: Description of the import format, human-readable.
        :param mimetype: MIME type of the import format.
        :param deserializer: Deserializer used to deserialize from the import format into record.
        :param oai_name: Optional tuple specifying the OAI-PMH namespace and local name of the
                 metadata element of oai-pmh xml record.
        """
        super().__init__(code)
        # stored as a single mapping, applied verbatim to the runtime's
        # Import dataclass in apply(). Extra kwargs are accepted but ignored
        # for backwards compatibility (see smells.md P1-9).
        self._options: dict[str, Any] = {
            "code": code,
            "name": name,
            "mimetype": mimetype,
            "deserializer": deserializer,
            "description": description,
            "oai_name": oai_name,
        }

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        builder.get_list("imports").append(Import(**self._options))
