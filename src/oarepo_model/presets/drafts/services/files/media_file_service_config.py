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

from invenio_records_resources.services import (
    FileServiceConfig,
)

from oarepo_model.customizations import AddClass, AddMixins, AddToList, Customization
from oarepo_model.model import Dependency, InvenioModel, ModelMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class MediaFileServiceConfigPreset(Preset):
    """
    Preset for file service config class.
    """

    provides = [
        "MediaFileServiceConfig",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        class MediaFileServiceConfigMixin(ModelMixin):
            service_id = f"{builder.model.base_name}-media-files"
            record_cls = Dependency("RecordMediaFiles")
            permission_policy_cls = Dependency("PermissionPolicy")
            permission_action_prefix = "media_"
            allow_upload = False

        yield AddClass("MediaFileServiceConfig", clazz=FileServiceConfig)
        yield AddMixins("MediaFileServiceConfig", MediaFileServiceConfigMixin)

        yield AddToList(
            "primary_record_service",
            lambda runtime_dependencies: (
                runtime_dependencies.get("RecordMediaFiles"),
                runtime_dependencies.get("MediaFileServiceConfig").service_id,
            ),
        )
