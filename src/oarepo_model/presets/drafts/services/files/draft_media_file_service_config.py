# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

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
from invenio_records_resources.services.files.links import FileEndpointLink
from invenio_records_resources.services.records.links import RecordEndpointLink

from oarepo_model.customizations import AddClass, AddToList, Customization, PrependMixin
from oarepo_model.model import Dependency, InvenioModel, ModelMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping

    from oarepo_model.builder import InvenioModelBuilder


class DraftMediaFileServiceConfigPreset(Preset):
    """Preset for file service config class."""

    provides = ("DraftMediaFileServiceConfig",)
    modifies = ("primary_record_service",)

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
            # unlike the published media config, draft media files are meant to be uploadable
            # (upstream invenio_rdm_records draft media config leaves this True too) - inherits
            # True from FileServiceConfig.allow_upload.

            file_links_list: Mapping[str, RecordEndpointLink] = {
                "self": RecordEndpointLink(
                    f"{model.base_name}_draft_media_files.search",
                    params=["pid_value"],
                ),
                "files-archive": RecordEndpointLink(
                    f"{model.base_name}_draft_media_files.read_archive",
                    params=["pid_value"],
                ),
            }

            file_links_item: Mapping[str, FileEndpointLink] = {
                "self": FileEndpointLink(
                    f"{model.base_name}_draft_media_files.read",
                    params=["pid_value", "key"],
                ),
                "content": FileEndpointLink(
                    f"{model.base_name}_draft_media_files.read_content",
                    params=["pid_value", "key"],
                ),
                "commit": FileEndpointLink(
                    f"{model.base_name}_draft_media_files.create_commit",
                    params=["pid_value", "key"],
                ),
            }

        yield AddClass("DraftMediaFileServiceConfig", clazz=FileServiceConfig)
        yield PrependMixin("DraftMediaFileServiceConfig", DraftMediaFileServiceConfigMixin)

        yield AddToList(
            "primary_record_service",
            lambda runtime_dependencies: (
                runtime_dependencies.get("DraftMediaFiles"),
                runtime_dependencies.get("DraftMediaFileServiceConfig").service_id,
            ),
        )
