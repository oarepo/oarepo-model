#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Customization for creating new lists in the model.

This module provides the AddList customization that creates new empty lists
in the model builder with specified names. The lists can then be populated
by other customizations or used to collect related items during model building.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, override

from oarepo_model.errors import (
    AlreadyRegisteredError,
)

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddFacetGroup(Customization):
    """Customization to add a list to the model."""

    def __init__(
        self,
        name: str,
        facets: list,
        exists_ok: bool = False,
    ) -> None:
        """Initialize the AddList customization.

        :param name: The name of the list to be added.
        :param exists_ok: Whether to ignore if the list already exists.
        """
        super().__init__(name)
        self.facets = facets
        self.exists_ok = exists_ok

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        """Add facet group."""
        facet_groups = builder.add_dictionary("FacetGroups", exists_ok=True)

        fg_typed: dict[str, list] = cast("dict[str, list]", facet_groups)

        if self.name in fg_typed:
            if self.exists_ok:
                fg_typed[self.name] = self.facets
            else:
                raise AlreadyRegisteredError(f"Facet group {self.name} already exists.")
        else:
            fg_typed[self.name] = self.facets
