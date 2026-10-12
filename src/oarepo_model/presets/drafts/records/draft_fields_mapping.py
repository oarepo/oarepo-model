# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Presets adding parent mapping to Opensearch mapping configuration of records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import Customization, PatchJSONFile
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftFieldsMappingPreset(Preset):
    """Preset for adding mapping fields required in records of drafts-supporting models."""

    modifies = ("record-mapping",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:

        additional_mapping = {
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
                    "publication_status": {"type": "keyword"},
                    "is_published": {"type": "boolean"},
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
        yield PatchJSONFile("record-mapping", additional_mapping)
