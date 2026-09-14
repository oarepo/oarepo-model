# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for configuring media file service.

This module provides a preset that creates and configures a MediaFileServiceConfig
for handling media files on published records. It sets up service identification,
permission policies, and disables uploads as media files are typically read-only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.services import (
    FileServiceConfig,
)

from oarepo_model.customizations import AddClass, AddToList, Customization, PrependMixin
from oarepo_model.model import Dependency, InvenioModel, ModelMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder


class MediaFileServiceConfigPreset(Preset):
    """Preset for file service config class."""

    provides = ("MediaFileServiceConfig",)
    modifies = ("primary_record_service",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class MediaFileServiceConfigMixin(ModelMixin):
            service_id = f"{builder.model.base_name}-media-files"
            record_cls = Dependency("RecordMediaFiles")
            permission_policy_cls = Dependency("PermissionPolicy")
            permission_action_prefix = "media_"
            # published media files are read-only: uploads/changes only ever happen on the draft
            # (see DraftMediaFileServiceConfig), then get published as-is.
            allow_upload = False

        yield AddClass("MediaFileServiceConfig", clazz=FileServiceConfig)
        yield PrependMixin("MediaFileServiceConfig", MediaFileServiceConfigMixin)

        yield AddToList(
            "primary_record_service",
            lambda runtime_dependencies: (
                runtime_dependencies.get("RecordMediaFiles"),
                runtime_dependencies.get("MediaFileServiceConfig").service_id,
            ),
        )
