#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for configuring draft file service.

This module provides a preset that creates and configures a DraftFileServiceConfig
for handling regular files on draft records. It includes service identification,
permission policies, and file link configurations for draft file operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, override

from invenio_records_resources.services import (
    FileServiceConfig,
)
from invenio_records_resources.services.files.links import FileEndpointLink
from invenio_records_resources.services.records.links import RecordEndpointLink

from oarepo_model.customizations import AddClass, AddToList, Customization, PrependMixin
from oarepo_model.model import Dependency, InvenioModel, ModelMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder


class DraftFileServiceConfigPreset(Preset):
    """Preset for file service config class."""

    provides = ("DraftFileServiceConfig",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class DraftFileServiceConfigMixin(ModelMixin):
            service_id = f"{builder.model.base_name}-draft-files"
            record_cls = Dependency("Draft")
            permission_policy_cls = Dependency("PermissionPolicy")
            permission_action_prefix = "draft_"

            file_links_list: ClassVar[dict[str, RecordEndpointLink]] = {
                "self": RecordEndpointLink(
                    f"{model.base_name}_draft_files.search",
                    params=["pid_value"],
                ),
                "files-archive": RecordEndpointLink(
                    f"{model.base_name}_draft_files.read_archive",
                    params=["pid_value"],
                ),
            }

            file_links_item: ClassVar[dict[str, FileEndpointLink]] = {
                "self": FileEndpointLink(
                    f"{model.base_name}_draft_files.read",
                    params=["pid_value", "key"],
                ),
                "content": FileEndpointLink(
                    f"{model.base_name}_draft_files.read_content",
                    params=["pid_value", "key"],
                ),
                "commit": FileEndpointLink(
                    f"{model.base_name}_draft_files.create_commit",
                    params=["pid_value", "key"],
                ),
            }

        yield AddClass("DraftFileServiceConfig", clazz=FileServiceConfig)
        yield PrependMixin("DraftFileServiceConfig", DraftFileServiceConfigMixin)

        yield AddToList(
            "primary_record_service",
            lambda runtime_dependencies: (
                runtime_dependencies.get("FileDraft"),
                runtime_dependencies.get("DraftFileServiceConfig").service_id,
            ),
        )
