# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Metadata UI schema preset for Invenio record serialization.

This module provides a preset that extends the base RecordUISchema with metadata-specific
functionality. It includes:

- MetadataUISchemaPreset: A preset that modifies the RecordUISchema to include metadata
  handling capabilities
- RecordMetadataUIMixin: A mixin class that adds a nested metadata field and flattens
  metadata fields to the top level during serialization

The preset automatically handles metadata schema generation based on the model's
metadata_type and ensures that metadata fields are properly flattened for UI consumption.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

import marshmallow

from oarepo_model.customizations import Customization, PrependMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class MetadataUISchemaPreset(Preset):
    """Preset for Metadata UI Schema."""

    modifies = ("RecordUISchema",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        if model.metadata_type is not None:
            from .ui_record_schema import get_ui_marshmallow_schema

            class RecordMetadataUIMixin(marshmallow.Schema):
                """Mixin for record UI schema which serializes metadata."""

                metadata = marshmallow.fields.Nested(get_ui_marshmallow_schema(builder, model.metadata_type))

                @marshmallow.post_dump()
                def flatten_metadata(
                    self,
                    data: dict[str, Any],
                    **_kwargs: Any,
                ) -> dict[str, Any]:
                    """Flatten metadata fields to the top level.

                    InvenioRDM uses a hand-written serialization approach that places
                    serialized metadata fields directly under the UI element,
                    rather than nesting them under a "metadata" key. To maintain
                    compatibility with this behavior while still generating the schema
                    automatically, we flatten the metadata fields to the top level
                    in the serialized output.

                    Input:

                    ```json
                    {
                        a: blah,
                        metadata: {
                            field1: value1,
                            ...
                        },
                    }
                    ```

                    Output:
                    ```json
                    {
                        a: blah
                        metadata: {
                            field1: value1,
                            ...
                        },
                        ui: {
                            a: uiblah,
                            field1: uivalue1,
                            ...
                        }
                    }
                    ```
                    """
                    metadata = data.pop("metadata", {})
                    for key, value in metadata.items():
                        if key not in data:
                            data[key] = value

                    return data

            yield PrependMixin("RecordUISchema", RecordMetadataUIMixin)
