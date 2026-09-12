# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Custom fields presets for OARepo models.

This package provides presets for adding custom fields functionality to OARepo models,
including support for extensible record schemas and dynamic field configurations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources import __version__

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


class CustomFieldsFeaturePreset(Preset):
    """Preset for enabling custom fields feature."""

    modifies = ("Ext",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class CustomFieldsFeatureMixin(RecordExtensionProtocol):
            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                parent_model_args = super().model_arguments
                return {
                    **parent_model_args,
                    "features": {
                        **parent_model_args["features"],
                        "custom-fields": {"version": __version__},
                    },
                }

        yield PrependMixin("Ext", CustomFieldsFeatureMixin)
