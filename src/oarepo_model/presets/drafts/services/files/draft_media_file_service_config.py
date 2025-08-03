#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for configuring draft media file service.

This module provides a preset that creates and configures a DraftMediaFileServiceConfig
for handling media files on draft records. It sets up service identification,
permission policies with draft-specific prefixes, and disables uploads.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.services import (
    FileServiceConfig,
)

from oarepo_model.customizations import AddClass, AddMixins, AddToList, Customization
from oarepo_model.model import Dependency, InvenioModel, ModelMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder


class DraftMediaFileServiceConfigPreset(Preset):
    """Preset for file service config class."""

    provides = ("DraftMediaFileServiceConfig",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class DraftMediaFileServiceConfigMixin(ModelMixin):
            service_id = f"{builder.model.base_name}-draft-media-files"
            record_cls = Dependency("DraftMediaFiles")
            permission_policy_cls = Dependency("PermissionPolicy")
            permission_action_prefix = "draft_media_"
            allow_upload = False

        yield AddClass("DraftMediaFileServiceConfig", clazz=FileServiceConfig)
        yield AddMixins("DraftMediaFileServiceConfig", DraftMediaFileServiceConfigMixin)

        yield AddToList(
            "primary_record_service",
            lambda runtime_dependencies: (
                runtime_dependencies.get("DraftMediaFiles"),
                runtime_dependencies.get("DraftMediaFileServiceConfig").service_id,
            ),
        )
