#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for adding resource error handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from flask_resources import HTTPJSONException, create_error_handler
from oarepo_runtime.errors import AuthExceptionGroup

from oarepo_model.customizations import AddToDictionary, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class ErrorHandlersPreset(Preset):
    """Preset for handling errors."""

    modifies = ("record_error_handlers",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddToDictionary(
            "record_error_handlers",
            {
                AuthExceptionGroup: create_error_handler(
                    lambda exc: HTTPJSONException(
                        code=401,
                        description=str(exc),
                    )
                ),
            },
        )
