#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Extension preset for file handling functionality in published records.

This module provides the ExtFilesPreset that configures
the Flask extension for handling files in published record repositories.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, override

from oarepo_runtime.config import build_config

import oarepo_model
from oarepo_model.customizations import (
    AddMixins,
    AddToList,
    Customization,
)
from oarepo_model.model import InvenioModel, ModelMixin
from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.ext import RecordExtensionProtocol

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask import Flask
    from invenio_records_resources.resources.files import FileResource
    from invenio_records_resources.services.files import FileService

    from oarepo_model.builder import InvenioModelBuilder


class RecordWithFilesExtensionProtocol(RecordExtensionProtocol):
    """Protocol for record extensions with files support."""

    @property
    def files_service(self) -> FileService:
        """File service instance."""
        return super().files_service  # type: ignore[no-any-return,misc] # pragma: no cover


class ExtFilesPreset(Preset):
    """Preset for extension class."""

    modifies = ("Ext",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class ExtFilesMixin(ModelMixin, RecordExtensionProtocol):
            """Mixin for extension class."""

            app: Flask

            @cached_property
            def files_service(self) -> FileService:
                return self.get_model_dependency("FileService")(
                    **self.files_service_params,
                )

            @property
            def files_service_params(self) -> dict[str, Any]:
                """Parameters for the file service."""
                return {
                    "config": build_config(
                        self.get_model_dependency("FileServiceConfig"),
                        self.app,
                    ),
                }

            @cached_property
            def files_resource(self) -> FileResource:
                return self.get_model_dependency("FileResource")(
                    **self.files_resource_params,
                )

            @property
            def files_resource_params(self) -> dict[str, Any]:
                """Parameters for the file resource."""
                return {
                    "service": self.files_service,
                    "config": build_config(
                        self.get_model_dependency("FileResourceConfig"),
                        self.app,
                    ),
                }

            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                parent_model_args = super().model_arguments
                return {
                    **parent_model_args,
                    "features": {
                        **parent_model_args["features"],
                        "files": {"version": oarepo_model.__version__},
                    },
                    "file_service": self.files_service,
                }

        yield AddMixins("Ext", ExtFilesMixin)

        yield AddToList(
            "services_registry_list",
            (
                lambda ext: ext.files_service,
                lambda ext: ext.files_service.config.service_id,
            ),
        )
