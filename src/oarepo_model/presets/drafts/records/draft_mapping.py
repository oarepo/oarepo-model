#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for draft record Opensearch mapping configuration.

This module provides the DraftMappingPreset that configures
Opensearch mappings for draft records in Invenio applications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import CopyFile, Customization, PatchJSONFile
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftMappingPreset(Preset):
    """Preset for record service class."""

    depends_on = ("record-mapping",)
    provides = ("draft-mapping",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield CopyFile(
            source_symbolic_name="record-mapping",
            target_symbolic_name="draft-mapping",
            target_module_name="mappings",
            target_file_path=f"os-v2/{model.base_name}/draft-metadata-v{model.version}.json",
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
                        },
                    },
                    "has_draft": {"type": "boolean"},
                    "record_status": {"type": "keyword"},
                    "pid": {
                        "properties": {
                            "obj_type": {"type": "keyword", "index": False},
                            "pid_type": {"type": "keyword", "index": False},
                            "pk": {"type": "long", "index": False},
                            "status": {"type": "keyword", "index": False},
                        },
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
                                },
                            },
                        },
                    },
                },
            },
        }

        yield PatchJSONFile("draft-mapping", parent_mapping)

        yield PatchJSONFile("record-mapping", parent_mapping)
