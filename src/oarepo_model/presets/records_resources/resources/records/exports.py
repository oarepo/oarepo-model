# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Exports preset for records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from flask_resources import (
    JSONSerializer,
)
from invenio_i18n import lazy_gettext as _

from oarepo_model.customizations import AddList, AddMetadataExport, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class ExportsPreset(Preset):
    """Preset for record metadata exports."""

    provides = ("exports",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddList(
            "exports",
        )
        yield AddMetadataExport(
            code="json",
            name=_("JSON"),
            mimetype="application/json",
            serializer=JSONSerializer(),
            display=True,
            oai_metadata_prefix=None,
            oai_schema=None,
            oai_namespace=None,
        )
