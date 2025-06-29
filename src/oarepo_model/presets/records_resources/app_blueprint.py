from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from oarepo_model.customizations import (
    AddDictionary,
    AddEntryPoint,
    AddModule,
    AddToModule,
    Customization,
)
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class AppBlueprintPreset(Preset):
    """
    Preset for app blueprint.
    """

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        yield AddModule("blueprints", exists_ok=True)

        yield AddDictionary("app_application_blueprint_initializers", exists_ok=True)

        dependencies = builder.get_runtime_dependencies()

        @staticmethod  # need to use staticmethod as python's magic always passes self as the first argument
        def create_app_blueprint(app):
            """Create DocumentsRecord blueprint."""
            with app.app_context():
                blueprint = app.extensions[
                    model.base_name
                ].records_resource.as_blueprint()

                for initializer_name, initializer_func in dependencies.get(
                    "app_application_blueprint_initializers"
                ).items():
                    blueprint.record_once(initializer_func)

            return blueprint

        yield AddToModule("blueprints", "create_app_blueprint", create_app_blueprint)

        yield AddEntryPoint(
            group="invenio_base.blueprints",
            name=model.base_name,
            value="blueprints:create_app_blueprint",
            separator=".",
        )
