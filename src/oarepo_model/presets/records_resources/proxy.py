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

from oarepo_model.customizations import AddModule, AddToModule, Customization
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class ProxyPreset(Preset):
    """
    Preset for proxy class.
    """

    provides = ["proxies"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
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
