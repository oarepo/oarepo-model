from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from oarepo_model.customizations import AddModule, AddToModule, Customization
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class ProxyPreset(Preset):
    """
    Preset for proxy class.
    """

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        build_dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        from flask import current_app
        from werkzeug.local import LocalProxy

        base_name = builder.model.base_name

        yield AddModule("proxies")
        yield AddToModule(
            "proxies", base_name, LocalProxy(lambda: current_app.extensions[base_name])
        )
        yield AddToModule(
            "proxies",
            "current_service",
            LocalProxy(lambda: current_app.extensions[base_name].records_service),
        )
        yield AddToModule(
            "proxies",
            "current_resource",
            LocalProxy(lambda: current_app.extensions[base_name].records_resource),
        )
