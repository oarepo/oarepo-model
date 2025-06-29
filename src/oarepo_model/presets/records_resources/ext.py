from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, Generator

from oarepo_runtime.config import build_config

from oarepo_model.customizations import (
    AddClass,
    AddEntryPoint,
    AddMixins,
    AddToDictionary,
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

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
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
                pass

            def init_config(self, app):
                """Initialize configuration."""

        class ServicesResourcesExtMixin(ModelMixin):
            """
            Mixin for extension class.
            """

            @cached_property
            def records_service(self):
                return self.get_model_dependency("RecordService")(
                    **self.records_service_params,
                )

            @property
            def records_service_params(self):
                """
                Parameters for the record service.
                """
                return {
                    "config": build_config(
                        self.get_model_dependency("RecordServiceConfig"), self.app
                    )
                }

            @cached_property
            def records_resource(self):
                return self.get_model_dependency("RecordResource")(
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
                        self.get_model_dependency("RecordResourceConfig"), self.app
                    ),
                }

        yield AddClass("Ext", clazz=ExtBase)
        yield AddMixins("Ext", ServicesResourcesExtMixin)

        yield AddEntryPoint("invenio_base.apps", model.base_name, "Ext")
        yield AddEntryPoint("invenio_base.api_apps", model.base_name, "Ext")

        def add_to_service_and_indexer_registry(state):
            """Init app."""
            app = state.app
            ext = app.extensions[model.base_name]

            # register service
            sregistry = app.extensions["invenio-records-resources"].registry
            service_id = ext.records_service.config.service_id
            if service_id not in sregistry._services:
                sregistry.register(ext.records_service, service_id=service_id)

            # Register indexer
            if hasattr(ext.records_service, "indexer"):
                iregistry = app.extensions["invenio-indexer"].registry
                if service_id not in iregistry._indexers:
                    iregistry.register(
                        ext.records_service.indexer,
                        indexer_id=ext.records_service.config.service_id,
                    )

        add_to_service_and_indexer_registry.__name__ = (
            f"{model.base_name}_add_to_service_and_indexer_registry"
        )

        yield AddToDictionary(
            "app_application_blueprint_initializers",
            "records_service",
            add_to_service_and_indexer_registry,
        )
        yield AddToDictionary(
            "api_application_blueprint_initializers",
            "records_service",
            add_to_service_and_indexer_registry,
        )
