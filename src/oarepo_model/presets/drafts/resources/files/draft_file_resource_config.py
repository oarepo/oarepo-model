#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for configuring draft file resource.

This module provides a preset that creates and configures a DraftFileResourceConfig
for draft file REST API endpoints. It sets up the blueprint name and URL prefix
for managing regular files on draft records.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.resources import FileResourceConfig

from oarepo_model.customizations import (
    AddClass,
    Customization,
    PrependMixin,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder


class DraftFileResourceConfigPreset(Preset):
    """Preset for file resource config class."""

    provides = ("DraftFileResourceConfig",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class DraftFileResourceConfigMixin:
            blueprint_name = f"{model.base_name}_draft_files"
            url_prefix = f"/{model.slug}/<pid_value>/draft"
            # Response handling
            response_handlers = Dependency("file_response_handlers")

        yield AddClass("DraftFileResourceConfig", clazz=FileResourceConfig)
        yield PrependMixin("DraftFileResourceConfig", DraftFileResourceConfigMixin)
