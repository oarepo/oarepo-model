#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""File to generate file resource configuration class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, override

from invenio_records_resources.resources import FileResourceConfig

from oarepo_model.customizations import (
    AddClass,
    AddDictionary,
    Customization,
    PrependMixin,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder


class FileResourceConfigPreset(Preset):
    """Preset for file resource config class."""

    provides = ("FileResourceConfig",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class FileResourceConfigMixin:
            blueprint_name = f"{model.base_name}_files"
            url_prefix = f"/{model.slug}/<pid_value>"
            # Response handling
            response_handlers = Dependency("file_response_handlers")

            response_handlers: ClassVar[dict] = {
                "application/vnd.inveniordm.v1+json": FileResourceConfig.response_handlers["application/json"],
                **FileResourceConfig.response_handlers,
            }

        yield AddClass("FileResourceConfig", clazz=FileResourceConfig)
        yield PrependMixin("FileResourceConfig", FileResourceConfigMixin)

        yield AddDictionary(
            "file_response_handlers",
            {**FileResourceConfig.response_handlers},
        )
