#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Base preset class for OARepo model presets.

This module provides the base Preset class that serves as the foundation for all
OARepo model presets. Presets define collections of customizations and configurations
that can be applied to models during the building process.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.customizations import Customization
    from oarepo_model.model import InvenioModel


class Preset:
    """Base class for presets."""

    provides: tuple[str, ...] = ()
    modifies: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    only_if: tuple[str, ...] = ()

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        """Apply the preset to the given model.

        This method should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @override
    def __repr__(self) -> str:
        """Return a string representation of the preset."""
        return f"{self.__class__.__name__}[{self.__class__.__module__}]"
