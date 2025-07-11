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
    Customization,
)
from oarepo_model.model import InvenioModel, ModelMixin
from oarepo_model.presets import Preset

from invenio_rdm_records.services.pids import PIDsService
from invenio_rdm_records.services.pids import PIDManager

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class ExtPreset(Preset):
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

        runtime_dependencies = builder.get_runtime_dependencies()

        class ServicesResourcesExtMixin(ModelMixin):
            """
            Mixin for extension class.
            """

            @cached_property
            def records_service(self):
                return runtime_dependencies.get("RecordService")(
                    **self.records_service_params,
                )

            @property # todo this is where we need to add the PIDsService
            def records_service_params(self):
                """
                Parameters for the record service.
                """
                config = build_config(
                        runtime_dependencies.get("RecordServiceConfig"), self.app
                    )
                # add
                return {
                    "pids_service": PIDsService(config, PIDManager)
                }

        yield AddMixins("Ext", ServicesResourcesExtMixin) # something like replace mixin but capable of replacing inner class or putting the args dict to some external modifiable configuration?