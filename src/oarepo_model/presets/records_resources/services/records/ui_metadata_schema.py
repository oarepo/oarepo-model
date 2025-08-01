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

import marshmallow

from oarepo_model.customizations import AddMixins, Customization
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder

class MetadataUISchemaPreset(Preset):
    """
    Preset for Metadata UI Schema.
    """
    
    modifies = ["RecordUISchema"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        
        if model.metadata_type is not None:
            from .ui_record_schema import get_ui_marshmallow_schema
            
            class RecordMetadataUIMixin(marshmallow.Schema):
                metadata = marshmallow.fields.Nested(get_ui_marshmallow_schema(builder, model.metadata_type))
                
                @marshmallow.post_dump()
                def flatten_metadata(self, data, **kwargs):
                    metadata = data.pop('metadata', {})
                    for key, value in metadata.items():
                        if key not in data:
                            data[key] = value

                    return data
                
            yield AddMixins("RecordUISchema", RecordMetadataUIMixin)
            
      
