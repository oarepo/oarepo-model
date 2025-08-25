#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Exports preset for records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from flask_resources import (
    JSONSerializer,
)
from invenio_i18n import lazy_gettext as _
from oarepo_runtime.api import Export

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
            Export(
                code="json",
                name=_("JSON"),
                mimetype="application/json",
                serializer=JSONSerializer(),
                display=True,
                oai_metadata_prefix=None,
                oai_schema=None,
                oai_namespace=None,
            ),
        )
