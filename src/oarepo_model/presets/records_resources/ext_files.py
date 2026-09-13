# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Extension preset for file handling functionality in published records.

This module provides the ExtFilesPreset that configures
the Flask extension for handling files in published record repositories.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, Protocol, override

from oarepo_runtime.config import build_config

import oarepo_model
from oarepo_model.customizations import (
    AddToList,
    Customization,
    PrependMixin,
)
from oarepo_model.model import InvenioModel, ModelMixin
from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.ext import RecordExtensionProtocol, RecordExtensionProtocolTyping

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask import Flask
    from invenio_records_resources.resources.files import FileResource
    from invenio_records_resources.services.files import FileService

    from oarepo_model.builder import InvenioModelBuilder


class RecordWithFilesExtensionProtocolTyping(RecordExtensionProtocolTyping, Protocol):
    """Structural shape adding 'files_service' on top of RecordExtensionProtocolTyping.

    Inherit RecordWithFilesExtensionProtocol below instead of this class, for
    the reason given in RecordExtensionProtocolTyping's docstring.
    """

    if TYPE_CHECKING:

        @property
        def files_service(self) -> FileService:
            """File service instance."""
            ...


if TYPE_CHECKING:
    RecordWithFilesExtensionProtocol = RecordWithFilesExtensionProtocolTyping
else:
    RecordWithFilesExtensionProtocol = object


class ExtFilesPreset(Preset):
    """Preset for extension class."""

    modifies = ("Ext", "services_registry_list")

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

        yield PrependMixin("Ext", ExtFilesMixin)

        yield AddToList(
            "services_registry_list",
            (
                lambda ext: ext.files_service,
                lambda ext: ext.files_service.config.service_id,
            ),
        )
