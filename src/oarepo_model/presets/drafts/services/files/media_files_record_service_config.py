#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from invenio_drafts_resources.services.records.config import (
    RecordServiceConfig,
)

from oarepo_model.customizations import (
    AddClass,
    AddClassList,
    AddMixins,
    Customization,
)
from oarepo_model.model import Dependency, InvenioModel, ModelMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class MediaFilesRecordServiceConfigPreset(Preset):
    """
    Preset for record service config class.
    """

    provides = [
        "MediaFilesRecordServiceConfig",
        "media_files_record_service_components",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        class MediaFilesRecordServiceConfigMixin(ModelMixin):

            record_cls = Dependency("Record")
            draft_cls = Dependency("Draft")

            service_id = f"{builder.model.base_name}_media_files"

            @property
            def components(self):
                # TODO: needs to be fixed as we have multiple mixins and the sources
                # in oarepo-runtime do not support this yet
                # return process_service_configs(
                #     self, self.get_model_dependency("record_service_components")
                # )
                return [
                    *super().components,
                    *self.get_model_dependency("media_files_record_service_components"),
                ]

            model = builder.model.name

        yield AddClassList("media_files_record_service_components", exists_ok=True)

        yield AddClass("MediaFilesRecordServiceConfig", clazz=RecordServiceConfig)
        yield AddMixins(
            "MediaFilesRecordServiceConfig", MediaFilesRecordServiceConfigMixin
        )
