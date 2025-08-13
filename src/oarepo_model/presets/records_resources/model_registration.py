#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for registering model to oarepo-runtime."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import AddDictionary, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class ModelRegistrationPreset(Preset):
    """Preset for model registration.

    This preset provides a dictionary of arguments to pass to the constructor
    of `oarepo_runtime.api.Model`. An instance of the model will then be registered
    via `OAREPO_MODELS` configuation. This is done during init_config inside the ext.py
    """

    provides = ("oarepo_model_arguments",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddDictionary(
            "oarepo_model_arguments",
            {
                "code": model.base_name,
                "name": model.name,
                "description": model.description,
                "version": model.version,
            },
        )
