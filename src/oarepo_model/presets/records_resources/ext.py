#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, Generator

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
    from oarepo_model.builder import InvenioModelBuilder


class ExtPreset(Preset):
    """
    Preset for extension class.
    """

    provides = [
        "Ext",
    ]

    modifies = [
        "app_application_blueprint_initializers",
        "api_application_blueprint_initializers",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        runtime_dependencies = builder.get_runtime_dependencies()

        class ExtBase:
            """
            Base class for extension.
            """

            def __init__(self, app=None):
                if app:
                    self.init_app(app)

            def init_app(self, app):
                """Flask application initialization."""
                self.app = app

                self.init_config(app)
                app.extensions[builder.model.base_name] = self
                self.init_extensions(app)

            def init_extensions(self, app):
                """Initialize extensions."""
                # This method can be overridden in subclasses to initialize
                # additional extensions or services.
                pass

            def init_config(self, app):
                """Initialize configuration."""
                OAREPO_PRIMARY_RECORD_SERVICE = app.config.setdefault(
                    "OAREPO_PRIMARY_RECORD_SERVICE", {}
                )
                for record_service_getter in runtime_dependencies.get(
                    "primary_record_service",
                ):
                    record_class, record_service_id = record_service_getter(
                        runtime_dependencies
                    )
                    if record_class not in OAREPO_PRIMARY_RECORD_SERVICE:
                        # Register the primary record service for the record class
                        # if it is not already registered.
                        OAREPO_PRIMARY_RECORD_SERVICE[record_class] = record_service_id

        class ServicesResourcesExtMixin(ModelMixin):
            """
            Mixin for extension class.
            """

            @cached_property
            def records_service(self):
                return runtime_dependencies.get("RecordService")(
                    **self.records_service_params,
                )

            @property
            def records_service_params(self):
                """
                Parameters for the record service.
                """
                return {
                    "config": build_config(
                        runtime_dependencies.get("RecordServiceConfig"), self.app
                    )
                }

            @cached_property
            def records_resource(self):
                return runtime_dependencies.get("RecordResource")(
                    **self.records_resource_params,
                )

            @property
            def records_resource_params(self):
                """
                Parameters for the record resource.
                """
                return {
                    "service": self.records_service,
                    "config": build_config(
                        runtime_dependencies.get("RecordResourceConfig"), self.app
                    ),
                }

            def init_config(self, app):
                super().init_config(app)

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

        def add_to_service_and_indexer_registry(state):
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
                if service_id not in sregistry._services:
                    sregistry.register(service, service_id=service_id)

            # Register indexer
            iregistry = app.extensions["invenio-indexer"].registry
            for indexer_getter, service_id_getter in runtime_dependencies.get(
                "indexers_registry_list",
            ):
                indexer = indexer_getter(ext)
                service_id = service_id_getter(ext)
                if indexer and service_id not in iregistry._indexers:
                    iregistry.register(indexer, indexer_id=service_id)

        add_to_service_and_indexer_registry.__name__ = (
            f"{model.base_name}_add_to_service_and_indexer_registry"
        )

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
