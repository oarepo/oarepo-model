# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

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

        def _get_deserializer() -> JSONDeserializer:
            """Get the JSON deserializer from the runtime dependencies.

            The .get needs to be called during runtime so a LazyProxy calling
            this function is used.
            """
            return runtime_dependencies.get("JSONDeserializer")()

        yield AddMetadataImport(
            code="json",
            name=_("JSON"),
            mimetype="application/json",
            deserializer=cast(
                "JSONDeserializer",
                LazyProxy(_get_deserializer),
            ),
            description=_("json import"),
        )
