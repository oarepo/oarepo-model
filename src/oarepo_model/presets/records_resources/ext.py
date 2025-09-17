#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Extension preset for records and resources functionality.

This module provides the ExtPreset that configures the main Flask extension
for handling records, resources, and services in Invenio applications.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, override

from invenio_records_resources import __version__
from oarepo_runtime.api import Export, Model
from oarepo_runtime.config import build_config

from oarepo_model.customizations import (
    AddClass,
    AddEntryPoint,
    AddMixins,
    AddToDictionary,
    AddToList,
    Customization,
)
from oarepo_model.model import InvenioModel, ModelMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask import Flask
    from flask.blueprints import BlueprintSetupState
    from invenio_records_resources.resources.records import RecordResource
    from invenio_records_resources.services.records import RecordService

    from oarepo_model.builder import InvenioModelBuilder


class ExtPreset(Preset):
    """Preset for extension class."""

    provides = ("Ext",)

    modifies = (
        "app_application_blueprint_initializers",
        "api_application_blueprint_initializers",
    )

    @override
    def apply(  # noqa C901: complexity is high
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        runtime_dependencies = builder.get_runtime_dependencies()

        class ExtBase:
            """Base class for extension."""

            def __init__(self, app: Flask | None = None):
                if app:
                    self.init_app(app)

            def init_app(self, app: Flask) -> None:
                """Flask application initialization."""
                self.app = app

                self.init_config(app)
                app.extensions[builder.model.base_name] = self
                self.init_extensions(app)

            def init_extensions(self, app: Flask) -> None:
                """Initialize extensions."""
                # This method can be overridden in subclasses to initialize
                # additional extensions or services.

            def init_config(self, app: Flask) -> None:
                """Initialize configuration."""
                registered_models = app.config.setdefault("OAREPO_MODELS", {})
                if model.base_name not in registered_models:
                    registered_models[model.base_name] = self.model

            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                return {
                    "records_alias_enabled": model.configuration.get("records_alias_enabled", True),
                    "features": {"records": {"version": __version__}},
                    **runtime_dependencies.get("oarepo_model_arguments"),
                }

            @cached_property
            def model(self) -> Model:
                return Model(**self.model_arguments)

        class ServicesResourcesExtMixin(ModelMixin):
            """Mixin for extension class."""

            app: Flask

            @cached_property
            def records_service(self) -> RecordService:
                return runtime_dependencies.get("RecordService")(
                    **self.records_service_params,
                )

            @property
            def records_service_params(self) -> dict[str, Any]:
                """Parameters for the record service."""
                return {
                    "config": build_config(
                        runtime_dependencies.get("RecordServiceConfig"),
                        self.app,
                    ),
                }

            @cached_property
            def records_resource(self) -> RecordResource:
                return runtime_dependencies.get("RecordResource")(
                    **self.records_resource_params,
                )

            @property
            def records_resource_params(self) -> dict[str, Any]:
                """Parameters for the record resource."""
                return {
                    "service": self.records_service,
                    "config": build_config(
                        runtime_dependencies.get("RecordResourceConfig"),
                        self.app,
                    ),
                }

            @property
            def metadata_exports(self) -> list[Export]:
                return runtime_dependencies.get("exports")  # type: ignore[no-any-return]

            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                return {
                    **super().model_arguments,  # type: ignore[misc] # pyright: ignore[reportAttributeAccessIssue]
                    "service": self.records_service,
                    "service_config": self.records_service.config,
                    "resource_config": self.records_resource.config,
                    "resource": self.records_resource,
                    "exports": self.metadata_exports,
                }

            def init_config(self, app: Flask) -> None:
                super().init_config(app)  # type: ignore[misc]

        yield AddClass("Ext", clazz=ExtBase)
        yield AddMixins("Ext", ServicesResourcesExtMixin)

        yield AddEntryPoint("invenio_base.apps", model.base_name, "Ext")
        yield AddEntryPoint("invenio_base.api_apps", model.base_name, "Ext")

        yield AddToList(
            "services_registry_list",
            (
                lambda ext: ext.records_service,
                lambda ext: ext.records_service.config.service_id,
            ),
        )

        yield AddToList(
            "indexers_registry_list",
            (
                lambda ext: getattr(ext.records_service, "indexer", None),
                lambda ext: ext.records_service.config.service_id,
            ),
        )

        def add_to_service_and_indexer_registry(state: BlueprintSetupState) -> None:
            """Init app."""
            app = state.app
            ext = app.extensions[model.base_name]

            # register service
            sregistry = app.extensions["invenio-records-resources"].registry
            for service_getter, service_id_getter in runtime_dependencies.get(
                "services_registry_list",
            ):
                service = service_getter(ext)
                service_id = service_id_getter(ext)
                if (
                    service_id not in sregistry._services  # noqa: SLF001 private member access
                ):
                    sregistry.register(service, service_id=service_id)

            # Register indexer
            iregistry = app.extensions["invenio-indexer"].registry
            for indexer_getter, service_id_getter in runtime_dependencies.get(
                "indexers_registry_list",
            ):
                indexer = indexer_getter(ext)
                service_id = service_id_getter(ext)
                if (
                    indexer and service_id not in iregistry._indexers  # noqa: SLF001 private member access
                ):
                    iregistry.register(indexer, indexer_id=service_id)

        add_to_service_and_indexer_registry.__name__ = f"{model.base_name}_add_to_service_and_indexer_registry"

        yield AddToDictionary(
            "app_application_blueprint_initializers",
            key="records_service",
            value=add_to_service_and_indexer_registry,
        )
        yield AddToDictionary(
            "api_application_blueprint_initializers",
            key="records_service",
            value=add_to_service_and_indexer_registry,
        )


class FilesFeaturePreset(Preset):
    """Preset for enabling files feature."""

    modifies = ("Ext",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class FilesFeatureMixin:
            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                parent_model_args = super().model_arguments  # type: ignore[misc] # pyright: ignore[reportAttributeAccessIssue]
                return {
                    **parent_model_args,
                    "features": {**parent_model_args["features"], "files": {"version": __version__}},
                }

        yield AddMixins("Ext", FilesFeatureMixin)


class RecordsFeaturePreset(Preset):
    """Preset for enabling records feature."""

    modifies = ("Ext",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class RecordsFeatureMixin:
            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                parent_model_args = super().model_arguments  # type: ignore[misc] # pyright: ignore[reportAttributeAccessIssue]
                return {
                    **parent_model_args,
                    "features": {**parent_model_args["features"], "records": {"version": __version__}},
                }

        yield AddMixins("Ext", RecordsFeatureMixin)
