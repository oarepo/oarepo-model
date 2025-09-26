#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for configuring draft-enabled record service.

This module provides a preset that extends the record service configuration
to support drafts functionality. It changes the base service config from
RecordServiceConfig to DraftServiceConfig and adds appropriate links for
draft operations like publish, edit, and version management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.services.records.config import is_record
from invenio_records_resources.services import (
    ConditionalLink,
    RecordEndpointLink,
)
from oarepo_runtime.services.config import (
    has_draft,
    has_permission,
)

from oarepo_model.customizations import (
    AddToDictionary,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftsUILinksPreset(Preset):
    """Preset for adding record ui links."""

    modifies = (
        "record_links_item",
        "record_search_item_links",
        "draft_search_links",
        "record_version_search_links",
    )
    only_if = ("Draft",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        ui_blueprint_name = model.configuration.get("ui_blueprint_name")
        if not ui_blueprint_name:
            return

        self_links = {
            "self_html": ConditionalLink(
                cond=is_record,
                if_=RecordEndpointLink(f"{ui_blueprint_name}.record_detail", when=has_permission("read")),
                else_=RecordEndpointLink(f"{ui_blueprint_name}.deposit_edit", when=has_permission("read_draft")),
            ),
            "edit_html": RecordEndpointLink(
                f"{ui_blueprint_name}.deposit_edit",
                when=has_permission("edit"),
            ),
            "preview_html": RecordEndpointLink(
                f"{ui_blueprint_name}.record_detail",
                vars=lambda _, vars_: vars_.update(
                    {
                        "args": {
                            "preview": "1",
                        }
                    }
                ),
                when=has_draft() & has_permission("read_draft"),
            ),
            "latest_html": RecordEndpointLink(
                f"{ui_blueprint_name}.latest",
                when=has_permission("read"),
            ),
        }

        yield AddToDictionary(
            "record_links_item",
            self_links,
        )

        yield AddToDictionary(
            "record_search_item_links",
            self_links,
        )

        # TODO: add draft_search_links when they are ready in oarepo-ui
        # TODO: add record_version_search_links when they are ready in oarepo-ui
