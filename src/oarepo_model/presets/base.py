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

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.customizations import Customization
    from oarepo_model.model import InvenioModel


class Preset:
    """
    Base class for presets.
    """

    provides: list[str] = []
    depends_on: list[str] = []

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        """
        Apply the preset to the given model.
        This method should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")
