#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""A module for defining the internal-relations feature preset."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_runtime import __version__

from oarepo_model.customizations import (
    Customization,
    PrependMixin,
)
from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.ext import RecordExtensionProtocol

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class InternalRelationsFeaturePreset(Preset):
    """Preset for enabling the internal-relations feature.

    Mirrors `presets/relations/ext.py`'s `RelationsFeaturePreset` - records the
    `oarepo_runtime` version (the package `InternalRelation`/`InternalRelations`
    actually come from) under the "internal-relations" feature key, so
    consumers can introspect whether/which version of internal relations a
    model has enabled via its `features` metadata, the same way they already
    can for "relations".
    """

    modifies = ("Ext",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        """Prepend a mixin recording the "internal-relations" feature onto the Ext class."""

        class InternalRelationsFeatureMixin(RecordExtensionProtocol):
            """Mixin adding the "internal-relations" entry to the extension's `features`."""

            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                parent_model_args = super().model_arguments
                return {
                    **parent_model_args,
                    "features": {
                        **parent_model_args["features"],
                        "internal-relations": {"version": __version__},
                    },
                }

        yield PrependMixin("Ext", InternalRelationsFeatureMixin)
