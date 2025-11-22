#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Extension preset for draft file handling functionality.

This module provides the ExtDraftFilesPreset that configures
the Flask extension for handling draft files in Invenio applications.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, cast, override

from oarepo_runtime.config import build_config

from oarepo_model.customizations import (
    AddToList,
    Customization,
    PrependMixin,
)
from oarepo_model.model import InvenioModel, ModelMixin
from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.ext_files import (
    RecordWithFilesExtensionProtocol,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask import Flask
    from invenio_records_resources.resources.files import FileResource
    from invenio_records_resources.services.files import FileService

    from oarepo_model.builder import InvenioModelBuilder


class ExtDraftFilesPreset(Preset):
    """Preset for extension class."""

    modifies = ("Ext",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class ExtDraftFilesMixin(ModelMixin, RecordWithFilesExtensionProtocol):
            """Mixin for extension class."""

            app: Flask

            @cached_property
            def draft_files_service(self) -> FileService:
                return cast(
                    "FileService",
                    self.get_model_dependency("DraftFileService")(
                        **self.draft_files_service_params,
                    ),
                )

            @property
            def draft_files_service_params(self) -> dict[str, Any]:
                """Parameters for the file service."""
                return {
                    "config": build_config(
                        self.get_model_dependency("DraftFileServiceConfig"),
                        self.app,
                    ),
                }

            @cached_property
            def draft_files_resource(self) -> FileResource:
                return self.get_model_dependency("DraftFileResource")(
                    **self.draft_files_resource_params,
                )

            @property
            def draft_files_resource_params(self) -> dict[str, Any]:
                """Parameters for the file resource."""
                return {
                    "service": self.draft_files_service,
                    "config": build_config(
                        self.get_model_dependency("DraftFileResourceConfig"),
                        self.app,
                    ),
                }

            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                return {
                    **super().model_arguments,
                    "draft_file_service": self.draft_files_service,
                }

            @property
            def records_service_params(self) -> dict[str, Any]:
                """Parameters for the record service."""
                params = super().records_service_params
                return {
                    **params,
                    "draft_files_service": self.draft_files_service,
                    "files_service": self.files_service,
                }

        yield PrependMixin("Ext", ExtDraftFilesMixin)

        yield AddToList(
            "services_registry_list",
            (
                lambda ext: ext.draft_files_service,
                lambda ext: ext.draft_files_service.config.service_id,
            ),
        )
