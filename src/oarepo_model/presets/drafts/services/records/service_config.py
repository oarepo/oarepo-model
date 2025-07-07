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

from invenio_drafts_resources.services import (
    RecordServiceConfig as DraftRecordServiceConfig,
)
from invenio_records_resources.services import (
    ConditionalLink,
    RecordLink,
)
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
    from oarepo_model.builder import InvenioModelBuilder


class DraftRecordServiceConfigPreset(Preset):
    """
    Preset for record service config class.
    """

    modifies = [
        "RecordServiceConfig",
        "record_links_item",
        "record_search_item",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        class DraftServiceConfigMixin(ModelMixin):
            draft_cls = Dependency("DraftRecord")

        yield ChangeBase(
            "RecordServiceConfig", RecordServiceConfig, DraftRecordServiceConfig
        )
        yield AddMixins("RecordServiceConfig", DraftServiceConfigMixin)

        api_base = "{+api}/" + builder.model.slug + "/"
        ui_base = "{+ui}/" + builder.model.slug + "/"

        api_url = api_base + "{id}"
        ui_url = ui_base + "{id}"

        self_links = {
            "self": ConditionalLink(
                cond=is_published_record(),
                if_=RecordLink(api_url, when=has_permission("read")),
                else_=RecordLink(api_url + "/draft", when=has_permission("read_draft")),
            ),
            "self_html": ConditionalLink(
                cond=is_published_record(),
                if_=RecordLink(ui_url, when=has_permission("read")),
                else_=RecordLink(
                    ui_url + "/preview", when=has_permission("read_draft")
                ),
            ),
        }

        yield AddToDictionary(
            "record_links_item",
            {
                **self_links,
                "latest": RecordLink(
                    api_url + "/versions/latest", when=has_permission("read")
                ),
                "latest_html": RecordLink(
                    ui_url + "/latest", when=has_permission("read")
                ),
                # Note: semantics change from oarepo v12: this link is only on a
                # published record if the record has a draft record
                "draft": RecordLink(
                    api_url + "/draft",
                    when=is_published_record()
                    & has_draft()
                    & has_draft_permission("read_draft"),
                ),
                "record": RecordLink(
                    api_url, when=has_published_record() & has_permission("read")
                ),
                "publish": RecordLink(
                    api_url + "/draft/actions/publish", when=has_permission("publish")
                ),
                "versions": RecordLink(
                    api_url + "/versions", when=has_permission("search_versions")
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
                runtime_dependencies.get("DraftRecord"),
                runtime_dependencies.get("RecordServiceConfig").service_id,
            ),
        )
