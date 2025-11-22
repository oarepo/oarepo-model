#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate record schema mixin with files metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

import marshmallow as ma
from marshmallow_utils.fields import (
    NestedAttribute,
)

from oarepo_model.customizations import Customization, PrependMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordWithFilesSchemaPreset(Preset):
    """Preset for record service class."""

    modifies = ("RecordSchema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class FilesSchema(ma.Schema):
            """Files metadata schema."""

            enabled = ma.fields.Bool()

            @override
            def get_attribute(self, obj: Any, attr: str, default: Any) -> Any:
                """Override how attributes are retrieved when dumping.

                NOTE: We have to access by attribute because although we are loading
                    from an external pure dict, but we are dumping from a data-layer
                    object whose fields should be accessed by attributes and not
                    keys. Access by key runs into FilesManager key access protection
                    and raises.
                """
                return getattr(obj, attr, default)

        class RecordWithFilesMixin(ma.Schema):
            files = NestedAttribute(FilesSchema)

        yield PrependMixin("RecordSchema", RecordWithFilesMixin)
