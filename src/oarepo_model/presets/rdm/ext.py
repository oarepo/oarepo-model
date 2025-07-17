#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, Generator

from oarepo_runtime.config import build_config

from oarepo_model.customizations import (
    AddClass,
    AddEntryPoint,
    AddMixins,
    AddToDictionary,
    AddToList,
    Customization, AddDictionary,
)
from oarepo_model.model import InvenioModel, ModelMixin
from oarepo_model.presets import Preset

from invenio_rdm_records.services.pids import PIDsService
from invenio_rdm_records.services.pids import PIDManager

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class RDMExtPreset(Preset):
    """
    Preset for extension class.
    """

    modifies = [
        "Ext"
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        class ExtRDMMixin(ModelMixin):

            @property
            def records_service_params(self):
                """
                Parameters for the record service.
                """
                params = super().records_service_params
                return {
                    **params,
                    "pids_service": PIDsService(params["config"], PIDManager),
                }

        yield AddMixins("Ext", ExtRDMMixin)