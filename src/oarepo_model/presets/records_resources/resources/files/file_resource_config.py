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

from invenio_records_resources.resources import FileResourceConfig

from oarepo_model.customizations import (
    AddClass,
    AddMixins,
    Customization,
)
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class FileResourceConfigPreset(Preset):
    """
    Preset for file resource config class.
    """

    provides = ["FileResourceConfig"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        class FileResourceConfigMixin:
            blueprint_name = f"{model.base_name}_files"
            url_prefix = f"/{model.slug}/<pid_value>"

        yield AddClass("FileResourceConfig", clazz=FileResourceConfig)
        yield AddMixins("FileResourceConfig", FileResourceConfigMixin)
