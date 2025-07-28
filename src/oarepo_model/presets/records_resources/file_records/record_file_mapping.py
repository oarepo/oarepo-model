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

from oarepo_model.customizations import Customization, PatchJSONFile
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class RecordFileMappingPreset(Preset):
    """
    Preset for record service class.
    """

    depends_on = ["metadata-mapping"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        file_mapping = {
            "mappings": {
                "properties": {
                    "files": {
                        "type": "object",
                        "properties": {
                            "enabled": {"type": "boolean"},
                        },
                    },
                    "media_files": {
                        "type": "object",
                        "properties": {
                            "enabled": {"type": "boolean"},
                        },
                    },
                    "bucket_id": {"type": "keyword", "index": False},
                    "media_bucket_id": {"type": "keyword", "index": False},
                }
            }
        }

        yield PatchJSONFile(
            "metadata-mapping",
            dependencies["metadata-mapping"]["module-name"],
            dependencies["metadata-mapping"]["file-path"],
            file_mapping,
        )
