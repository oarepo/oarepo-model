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
    AddMixins,
    AddToList,
    Customization,
)
from oarepo_model.model import InvenioModel, ModelMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class ExtMediaFilesPreset(Preset):
    """
    Preset for extension class.
    """

    modifies = [
        "Ext",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        class ExtMediaFilesMixin(ModelMixin):
            """
            Mixin for extension class.
            """

            @cached_property
            def media_files_service(self):
                return self.get_model_dependency("MediaFileService")(
                    **self.media_files_service_params,
                )

            @property
            def media_files_service_params(self):
                """
                Parameters for the file service.
                """
                return {
                    "config": build_config(
                        self.get_model_dependency("MediaFileServiceConfig"), self.app
                    )
                }

            @cached_property
            def media_files_resource(self):
                return self.get_model_dependency("MediaFileResource")(
                    **self.media_files_resource_params,
                )

            @property
            def media_files_resource_params(self):
                """
                Parameters for the file resource.
                """
                return {
                    "service": self.media_files_service,
                    "config": build_config(
                        self.get_model_dependency("MediaFileResourceConfig"), self.app
                    ),
                }

        yield AddMixins("Ext", ExtMediaFilesMixin)

        yield AddToList(
            "services_registry_list",
            (
                lambda ext: ext.media_files_service,
                lambda ext: ext.media_files_service.config.service_id,
            ),
        )
