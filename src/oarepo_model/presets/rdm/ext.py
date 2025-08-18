#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Extension preset for rdm functionality.

This module provides the RDMExtPreset that configures the main Flask extension
for handling records, resources, and services in Invenio applications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_rdm_records.services.pids import PIDManager, PIDsService

from oarepo_model.customizations import (
    AddMixins,
    Customization,
)
from oarepo_model.model import InvenioModel, ModelMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder


class RDMExtPreset(Preset):
    """Preset for extension class."""

    modifies = ("Ext",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class ExtRDMMixin(ModelMixin):
            @property
            def records_service_params(self) -> dict[str, Any]:
                """Parameters for the record service."""
                params = super().records_service_params  # type: ignore[misc]
                return {
                    **params,
                    "pids_service": PIDsService(params["config"], PIDManager),
                }

        yield AddMixins("Ext", ExtRDMMixin)
