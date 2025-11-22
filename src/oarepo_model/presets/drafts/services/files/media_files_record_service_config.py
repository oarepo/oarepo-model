#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for configuring media files record service.

This module provides a preset that creates a specialized record service configuration
for handling media files. It includes service components specific to media file
management and sets up the necessary configuration for media file operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from invenio_drafts_resources.services.records.config import (
    RecordServiceConfig,
)

from oarepo_model.customizations import (
    AddClass,
    AddClassList,
    Customization,
    PrependMixin,
)
from oarepo_model.model import Dependency, InvenioModel, ModelMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from invenio_records_resources.records.api import Record
    from invenio_records_resources.services.records.components import ServiceComponent
    from invenio_records_resources.services.records.config import (
        RecordServiceConfig as BaseRecordServiceConfig,
    )

    from oarepo_model.builder import InvenioModelBuilder
else:
    BaseRecordServiceConfig = object


class MediaFilesRecordServiceConfigPreset(Preset):
    """Preset for record service config class."""

    provides = (
        "MediaFilesRecordServiceConfig",
        "media_files_record_service_components",
    )

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class MediaFilesRecordServiceConfigMixin(ModelMixin, BaseRecordServiceConfig):
            record_cls = cast("type[Record]", Dependency("Record"))
            draft_cls = cast("type[Record]", Dependency("Draft"))

            service_id = f"{builder.model.base_name}_media_files"

            @property
            def components(self) -> list[type[ServiceComponent]]:  # type: ignore[]
                # TODO: needs to be fixed as we have multiple mixins and the sources
                # in oarepo-runtime do not support this yet
                # return process_service_configs(
                #     self, self.get_model_dependency("record_service_components")  # noqa
                return [
                    *super().components,
                    *cast(
                        "list[type[ServiceComponent]]",
                        self.get_model_dependency("media_files_record_service_components"),
                    ),
                ]

            model = builder.model.name

        yield AddClassList("media_files_record_service_components", exists_ok=True)

        yield AddClass("MediaFilesRecordServiceConfig", clazz=RecordServiceConfig)
        yield PrependMixin(
            "MediaFilesRecordServiceConfig",
            MediaFilesRecordServiceConfigMixin,
        )
