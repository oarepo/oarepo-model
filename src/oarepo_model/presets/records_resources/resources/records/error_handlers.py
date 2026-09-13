# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

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
                    lambda _exc: HTTPJSONException(
                        code=401,
                        description="Authentication failed.",
                    )
                ),
            },
        )
