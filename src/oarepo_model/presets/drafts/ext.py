#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Draft-related presets for Invenio draft/publish workflows.

This module provides presets for implementing draft record functionality,
including file handling, record management, and API blueprints for
draft-enabled Invenio repositories.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from invenio_drafts_resources import __version__

from oarepo_model.customizations import (
    AddMixins,
    Customization,
)

if TYPE_CHECKING:
    from oarepo_model.presets.base import Preset

from typing import TYPE_CHECKING, Any, override

from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.ext_files import (
    RecordWithFilesExtensionProtocol,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftsFilesFeaturePreset(Preset):
    """Preset for enabling drafts files feature."""

    modifies = ("Ext",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class DraftsFilesFeatureMixin(RecordWithFilesExtensionProtocol):
            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                return {
                    **super().model_arguments,
                    "features": {"drafts-files": {"version": __version__}},
                }

        yield AddMixins("Ext", DraftsFilesFeatureMixin)


class DraftsRecordsFeaturePreset(Preset):
    """Preset for enabling drafts records feature."""

    modifies = ("Ext",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class DraftsRecordsFeatureMixin(RecordWithFilesExtensionProtocol):
            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                parent_model_args = super().model_arguments
                return {
                    **parent_model_args,
                    "features": {
                        **parent_model_args["features"],
                        "drafts-records": {"version": __version__},
                    },
                }

        yield AddMixins("Ext", DraftsRecordsFeatureMixin)
