# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Extension preset for records and resources functionality.

This module provides the ExtPreset that configures the main Flask extension
for handling records, resources, and services in Invenio applications.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, Protocol, cast, override

from invenio_records_resources import __version__
from oarepo_runtime.api import Export, Import, Model
from oarepo_runtime.config import build_config

from oarepo_model.customizations import (
    AddClass,
    AddEntryPoint,
    AddToDictionary,
    AddToList,
    Customization,
    PrependMixin,
)
from oarepo_model.model import InvenioModel, ModelMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from flask import Flask
    from flask.blueprints import BlueprintSetupState
    from invenio_indexer.registry import IndexerRegistry
    from invenio_records_resources.registry import ServiceRegistry
    from invenio_records_resources.resources.records import RecordResource
    from invenio_records_resources.services.records import RecordService

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import RuntimeDependencies


def _register_entries(
    registry: ServiceRegistry | IndexerRegistry,
    entries: list[tuple[Callable[[Any], Any], Callable[[Any], str]]],
    ext: Any,
    register: Callable[[Any, Any, str], None],
) -> None:
    """Register getter/id-getter pairs into a registry, skipping already-registered ids."""
    for item_getter, id_getter in entries:
        item = item_getter(ext)
        if item is None:
            continue
        item_id = id_getter(ext)
        try:
            registry.get(item_id)
        except KeyError:
            register(registry, item, item_id)


class RecordExtensionProtocol(Protocol):
    """Protocol for flask extension with model arguments."""

    @property
    def model_arguments(self) -> dict[str, Any]:
        """Return model arguments for the extension."""
        return super().model_arguments  # pragma: no cover

    @property
    def records_service_params(self) -> dict[str, Any]:
        """Return parameters for the records service."""
        return super().records_service_params  # pragma: no cover

    def init_config(self, app: Flask) -> None:
        """Initialize configuration."""
        return super().init_config(app)


class ExtPreset(Preset):
    """Preset for extension class."""

    provides = ("Ext",)

    modifies = (
        "app_application_blueprint_initializers",
        "api_application_blueprint_initializers",
    )

    def _build_ext_base(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        runtime_dependencies: RuntimeDependencies,
    ) -> type:
        """Build the base extension class for the given model/builder."""

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
                    "namespace": builder.ns,
                    **runtime_dependencies.get("oarepo_model_arguments"),
                }

            @cached_property
            def model(self) -> Model:
                return Model(**self.model_arguments)

        return ExtBase

    def _build_services_mixin(self, runtime_dependencies: RuntimeDependencies) -> type:
        """Build the mixin adding records service/resource support to the extension."""

        class ServicesResourcesExtMixin(ModelMixin, RecordExtensionProtocol):
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
                return cast("list[Export]", runtime_dependencies.get("exports"))

            @property
            def metadata_imports(self) -> list[Import]:
                return cast("list[Import]", runtime_dependencies.get("imports"))

            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                return {
                    **super().model_arguments,
                    "service": self.records_service,
                    "service_config": self.records_service.config,
                    "resource_config": self.records_resource.config,
                    "resource": self.records_resource,
                    "exports": self.metadata_exports,
                    "imports": self.metadata_imports,
                }

            def init_config(self, app: Flask) -> None:
                super().init_config(app)

        return ServicesResourcesExtMixin

    def _build_registry_initializer(
        self,
        model: InvenioModel,
        runtime_dependencies: RuntimeDependencies,
    ) -> Callable[[BlueprintSetupState], None]:
        """Build the blueprint-setup callback registering services/indexers on first use."""

        def add_to_service_and_indexer_registry(state: BlueprintSetupState) -> None:
            """Init app."""
            app = state.app
            ext = app.extensions[model.base_name]

            # neither registry exposes a listing/contains check, but get() raises KeyError
            # for an id that has not been registered yet
            sregistry = cast("ServiceRegistry", app.extensions["invenio-records-resources"].registry)
            _register_entries(
                sregistry,
                runtime_dependencies.get("services_registry_list"),
                ext,
                lambda registry, item, item_id: registry.register(item, service_id=item_id),
            )

            iregistry = cast("IndexerRegistry", app.extensions["invenio-indexer"].registry)
            _register_entries(
                iregistry,
                runtime_dependencies.get("indexers_registry_list"),
                ext,
                lambda registry, item, item_id: registry.register(item, indexer_id=item_id),
            )

        add_to_service_and_indexer_registry.__name__ = f"{model.base_name}_add_to_service_and_indexer_registry"
        return add_to_service_and_indexer_registry

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        runtime_dependencies = builder.get_runtime_dependencies()

        ext_base = self._build_ext_base(builder, model, runtime_dependencies)
        services_mixin = self._build_services_mixin(runtime_dependencies)

        yield AddClass("Ext", clazz=ext_base)
        yield PrependMixin("Ext", services_mixin)

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

        add_to_service_and_indexer_registry = self._build_registry_initializer(model, runtime_dependencies)

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
        class FilesFeatureMixin(RecordExtensionProtocol):
            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                parent_model_args = super().model_arguments
                return {
                    **parent_model_args,
                    "features": {
                        **parent_model_args["features"],
                        "files": {"version": __version__},
                    },
                }

        yield PrependMixin("Ext", FilesFeatureMixin)


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
        class RecordsFeatureMixin(RecordExtensionProtocol):
            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                parent_model_args = super().model_arguments
                return {
                    **parent_model_args,
                    "features": {
                        **parent_model_args["features"],
                        "records": {"version": __version__},
                    },
                }

        yield PrependMixin("Ext", RecordsFeatureMixin)
