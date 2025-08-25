#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""High-level customization for adding metadata exports to models.

This module provides the AddMetadataExport customization that registers an export
serializer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ..base import Customization

if TYPE_CHECKING:
    from oarepo_runtime.api import Export

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddMetadataExport(Customization):
    """Customization to add metadata export to the model."""

    modifies = ("exports",)

    def __init__(self, export: Export):
        """Initialize the AddMetadataExport customization."""
        super().__init__("AddMetadataExport")
        self._export = export

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        exports = builder.get_list("exports")
        exports.append(self._export)
