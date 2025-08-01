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

import marshmallow as ma
from marshmallow_utils.fields import (
    NestedAttribute,
)

from oarepo_model.customizations import AddMixins, Customization
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class RecordWithFilesSchemaPreset(Preset):
    """
    Preset for record service class.
    """

    modifies = ["RecordSchema"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        class FilesSchema(ma.Schema):
            """Files metadata schema."""

            enabled = ma.fields.Bool()

            def get_attribute(self, obj, attr, default):
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

        yield AddMixins("RecordSchema", RecordWithFilesMixin)
