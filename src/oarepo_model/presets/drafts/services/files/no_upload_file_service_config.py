#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for disabling file uploads in file service configuration.

This module provides a preset that modifies the FileServiceConfig to disable
file uploads by setting allow_upload to False. This is useful for read-only
file services or when file uploads should be handled through different mechanisms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import AddMixins, Customization
from oarepo_model.model import InvenioModel, ModelMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder


class NoUploadFileServiceConfigPreset(Preset):
    """Preset for file service config class."""

    modifies = ("FileServiceConfig",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class NoUploadFileServiceConfigMixin(ModelMixin):
            allow_upload = False

        yield AddMixins("FileServiceConfig", NoUploadFileServiceConfigMixin)
