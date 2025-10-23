#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Imports preset for records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from invenio_i18n import lazy_gettext as _
from proxytypes import LazyProxy

from oarepo_model.customizations import AddList, AddMetadataImport, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask_resources import JSONDeserializer

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class ImportsPreset(Preset):
    """Preset for record metadata imports."""

    provides = ("imports",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        runtime_dependencies = builder.get_runtime_dependencies()
        yield AddList(
            "imports",
        )
        yield AddMetadataImport(
            code="json",
            name=_("JSON"),
            mimetype="application/json",
            deserializer=cast("JSONDeserializer", LazyProxy(lambda: runtime_dependencies.get("JSONDeserializer")())),
            description=_("json import"),
        )
