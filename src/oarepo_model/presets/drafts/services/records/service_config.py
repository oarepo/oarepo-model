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

from typing import TYPE_CHECKING, Any, cast, override

from invenio_drafts_resources.services import (
    RecordServiceConfig as DraftServiceConfig,
)
from invenio_rdm_records.services.config import (
    is_record,
)
from invenio_records_resources.services import (
    ConditionalLink,
    EndpointLink,
    Link,
    RecordEndpointLink,
    pagination_endpoint_links,
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
from oarepo_runtime.services.records.links import pagination_record_endpoint_links

from oarepo_model.customizations import (
    AddDictionary,
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

    from invenio_drafts_resources.records.api import Draft
    from invenio_drafts_resources.services.records.config import (
        RecordServiceConfig as DraftRecordServiceConfig,
    )

    from oarepo_model.builder import InvenioModelBuilder
else:
    DraftRecordServiceConfig = object


class DraftServiceConfigPreset(Preset):
    """Preset for record service config class."""

    modifies = (
        "RecordServiceConfig",
        "record_links_item",
        "record_search_item_links",
    )

    provides = (
        "draft_search_links",
        "record_version_search_links",
    )

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class DraftServiceConfigMixin(ModelMixin, DraftRecordServiceConfig):
            draft_cls = cast("type[Draft]", Dependency("Draft"))

            @property
            def links_search_drafts(self) -> dict[str, Link]:
                try:
                    supercls_links = super().links_search_drafts
                except AttributeError:  # if they aren't defined in the superclass
                    supercls_links = {}
                links = {
                    **supercls_links,
                    **self.get_model_dependency("draft_search_links"),
                }
                return {k: v for k, v in links.items() if v is not None}

            @property
            def links_search_versions(self) -> dict[str, Link]:
                try:
                    supercls_links = super().links_search_versions
                except AttributeError:  # if they aren't defined in the superclass
                    supercls_links = {}
                links = {
                    **supercls_links,
                    **self.get_model_dependency("record_version_search_links"),
                }
                return {k: v for k, v in links.items() if v is not None}

        yield ChangeBase("RecordServiceConfig", RecordServiceConfig, DraftServiceConfig)
        yield AddMixins("RecordServiceConfig", DraftServiceConfigMixin)

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
        }

        yield AddToDictionary(
            "record_links_item",
            {
                **self_links,
                "parent": EndpointLink(
                    f"{model.blueprint_base}.read",
                    params=["pid_value"],
                    when=is_record,
                    vars=lambda record, variables: variables.update({"pid_value": record.parent.pid.pid_value}),
                ),
                "latest": RecordEndpointLink(
                    f"{model.blueprint_base}.read_latest",
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
                    when=has_permission("publish") & has_draft(),
                ),
                "versions": RecordEndpointLink(
                    f"{model.blueprint_base}.search_versions",
                    when=has_permission("search_versions"),
                ),
            },
        )

        yield AddToDictionary(
            "record_search_item_links",
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

        yield AddDictionary(
            "draft_search_links",
            pagination_endpoint_links(f"{model.blueprint_base}.search_user_records"),
        )

        # We need <pid_value> to substitute into the url rule but search_versions adds <id> into the link template
        yield AddDictionary(
            "record_version_search_links",
            pagination_record_endpoint_links(f"{model.blueprint_base}.search_versions"),
        )
