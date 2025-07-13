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

from oarepo_model.customizations import CopyFile, Customization, PatchJSONFile
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class DraftMappingPreset(Preset):
    """
    Preset for record service class.
    """

    depends_on = ["RECORD_MAPPING_PATH"]
    provides = ["DRAFT_MAPPING_PATH"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        # TODO: the namespace_constant is not pretty
        yield CopyFile(
            source_module_name=dependencies["RECORD_MAPPING_PATH"][0],
            source_file_path=dependencies["RECORD_MAPPING_PATH"][1],
            target_module_name="mappings",
            target_file_path=f"os-v2/{model.base_name}/draft-metadata-v{model.version}.json",
            namespace_constant="DRAFT_MAPPING_PATH",
        )

        parent_mapping = {
            "mappings": {
                "properties": {
                    "bucket_id": {"type": "keyword", "index": False},
                    "versions": {
                        "properties": {
                            "index": {"type": "integer"},
                            "is_latest": {"type": "boolean"},
                            "is_latest_draft": {"type": "boolean"},
                            "latest_id": {"type": "keyword"},
                            "latest_index": {"type": "integer"},
                            "next_draft_id": {"type": "keyword"},
                        }
                    },
                    "has_draft": {"type": "boolean"},
                    "record_status": {"type": "keyword"},
                    "pid": {
                        "properties": {
                            "obj_type": {"type": "keyword", "index": False},
                            "pid_type": {"type": "keyword", "index": False},
                            "pk": {"type": "long", "index": False},
                            "status": {"type": "keyword", "index": False},
                        }
                    },
                    "fork_version_id": {"type": "long"},
                    "parent": {
                        "properties": {
                            "$schema": {"type": "keyword", "index": False},
                            "id": {"type": "keyword"},
                            "uuid": {"type": "keyword", "index": False},
                            "version_id": {"type": "long"},
                            "created": {"type": "date"},
                            "updated": {"type": "date"},
                            "pid": {
                                "properties": {
                                    "obj_type": {"type": "keyword", "index": False},
                                    "pid_type": {"type": "keyword", "index": False},
                                    "pk": {"type": "long", "index": False},
                                    "status": {"type": "keyword", "index": False},
                                }
                            },
                        }
                    },
                }
            }
        }

        yield PatchJSONFile(
            "mappings",
            f"os-v2/{model.base_name}/draft-metadata-v{model.version}.json",
            parent_mapping,
        )

        yield PatchJSONFile(
            dependencies["RECORD_MAPPING_PATH"][0],
            dependencies["RECORD_MAPPING_PATH"][1],
            parent_mapping,
        )
