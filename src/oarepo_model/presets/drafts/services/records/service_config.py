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

from invenio_drafts_resources.services import (
    RecordServiceConfig as DraftServiceConfig,
)
from invenio_records_resources.services import ConditionalLink, RecordEndpointLink, RecordLink
from invenio_records_resources.services.records.config import (
    RecordServiceConfig,
)
from oarepo_runtime.services.config import (
    has_draft,
    has_draft_permission,
    has_permission,
    has_published_record,
    is_published_record,
)

from oarepo_model.customizations import (
    AddMixins,
    AddToDictionary,
    AddToList,
    ChangeBase,
    Customization,
)
from oarepo_model.model import Dependency, InvenioModel, ModelMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder


class DraftServiceConfigPreset(Preset):
    """Preset for record service config class."""

    modifies = (
        "RecordServiceConfig",
        "record_links_item",
        "record_search_item",
    )

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class DraftServiceConfigMixin(ModelMixin):
            draft_cls = Dependency("Draft")

        yield ChangeBase("RecordServiceConfig", RecordServiceConfig, DraftServiceConfig)
        yield AddMixins("RecordServiceConfig", DraftServiceConfigMixin)

        ui_base = "{+ui}/" + builder.model.slug + "/"

        ui_url = ui_base + "{id}"

        self_links = {
            "self": ConditionalLink(
                cond=is_published_record(),
                if_=RecordEndpointLink(
                    f"{model.blueprint_base}.read",
                    when=has_permission("read"),
                ),
                else_=RecordEndpointLink(
                    f"{model.blueprint_base}.read_draft",
                    when=has_permission("read_draft"),
                ),
            ),
            "self_html": ConditionalLink(
                cond=is_published_record(),
                if_=RecordLink(ui_url, when=has_permission("read")),
                else_=RecordLink(
                    ui_url + "/preview",
                    when=has_permission("read_draft"),
                ),
            ),
        }

        yield AddToDictionary(
            "record_links_item",
            {
                **self_links,
                "latest": RecordEndpointLink(
                    f"{model.blueprint_base}.read_latest",
                    when=has_permission("read"),
                ),
                "latest_html": RecordLink(
                    ui_url + "/latest",
                    when=has_permission("read"),
                ),
                # Note: semantics change from oarepo v12: this link is only on a
                # published record if the record has a draft record
                "draft": RecordEndpointLink(
                    f"{model.blueprint_base}.read_draft",
                    when=is_published_record() & has_draft() & has_draft_permission("read_draft"),
                ),
                "record": RecordEndpointLink(
                    f"{model.blueprint_base}.read",
                    when=has_published_record() & has_permission("read"),
                ),
                "publish": RecordEndpointLink(
                    f"{model.blueprint_base}.publish",
                    when=has_permission("publish"),
                ),
                "versions": RecordEndpointLink(
                    f"{model.blueprint_base}.search_versions",
                    when=has_permission("search_versions"),
                ),
            },
        )

        yield AddToDictionary(
            "record_search_item",
            {
                **self_links,
            },
        )

        yield AddToList(
            "primary_record_service",
            lambda runtime_dependencies: (
                runtime_dependencies.get("Draft"),
                runtime_dependencies.get("RecordServiceConfig").service_id,
            ),
        )
