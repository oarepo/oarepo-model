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
from invenio_records_resources.services.files.links import FileEndpointLink
from invenio_records_resources.services.records.links import (
    RecordEndpointLink,
)

from oarepo_model.customizations import AddClass, AddMixins, AddToList, Customization
from oarepo_model.model import Dependency, InvenioModel, ModelMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class FileServiceConfigPreset(Preset):
    """
    Preset for file service config class.
    """

    provides = [
        "FileServiceConfig",
        "file_service_components",
        "file_links_item",
        "file_search_item",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        class FileServiceConfigMixin(ModelMixin):
            service_id = f"{builder.model.base_name}-files"
            record_cls = Dependency("Record")
            permission_policy_cls = Dependency("PermissionPolicy")

            file_links_list = {
                "self": RecordEndpointLink(
                    f"{model.base_name}_files.search", params=["pid_value"]
                ),
                "files-archive": RecordEndpointLink(
                    f"{model.base_name}_files.read_archive", params=["pid_value"]
                ),
            }

            file_links_item = {
                "self": FileEndpointLink(
                    f"{model.base_name}_files.read", params=["pid_value", "key"]
                ),
                "content": FileEndpointLink(
                    f"{model.base_name}_files.read_content", params=["pid_value", "key"]
                ),
                "commit": FileEndpointLink(
                    f"{model.base_name}_files.create_commit",
                    params=["pid_value", "key"],
                ),
            }

        yield AddClass("FileServiceConfig", clazz=FileServiceConfig)
        yield AddMixins("FileServiceConfig", FileServiceConfigMixin)

        yield AddToList(
            "primary_record_service",
            lambda runtime_dependencies: (
                runtime_dependencies.get("FileRecord"),
                runtime_dependencies.get("FileServiceConfig").service_id,
            ),
        )
