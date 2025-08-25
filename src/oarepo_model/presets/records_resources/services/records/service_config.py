#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate config for the record service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.services import (
    Link,
    LinksTemplate,
    RecordEndpointLink,
    RecordLink,
    pagination_endpoint_links,
)
from invenio_records_resources.services.records.config import (
    RecordServiceConfig,
)
from oarepo_runtime.services.config import (
    has_permission,
)
from oarepo_runtime.services.records import pagination_links_html

from oarepo_model.customizations import (
    AddClass,
    AddDictionary,
    AddList,
    AddMixins,
    AddToList,
    Customization,
)
from oarepo_model.model import Dependency, InvenioModel, ModelMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from invenio_records_resources.services.records.components import ServiceComponent

    from oarepo_model.builder import InvenioModelBuilder


class RecordServiceConfigPreset(Preset):
    """Preset for record service config class."""

    provides = (
        "RecordServiceConfig",
        "record_service_components",
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
        ui_base = "{+ui}/" + builder.model.slug + "/"

        ui_url = ui_base + "{id}"

        class ServiceConfigMixin(ModelMixin):
            result_item_cls = Dependency("RecordItem")
            result_list_cls = Dependency("RecordList")

            url_prefix = f"/{builder.model.slug}/"

            permission_policy_cls = Dependency("PermissionPolicy")

            schema = Dependency("RecordSchema")

            search = Dependency("RecordSearchOptions")

            record_cls = Dependency("Record")

            service_id = builder.model.base_name
            indexer_queue_name = f"{builder.model.base_name}_indexer"

            search_item_links_template = LinksTemplate

            @property
            def components(self) -> list[ServiceComponent]:
                # TODO: needs to be fixed as we have multiple mixins and the sources
                # in oarepo-runtime do not support this yet
                # return process_service_configs(
                #     self, self.get_model_dependency("record_service_components") # noqa: ERA001
                #
                return [
                    *super().components,  # type: ignore[misc]
                    *self.get_model_dependency("record_service_components"),
                ]

            model = builder.model.name

            @property
            def links_item(self) -> dict[str, Link]:
                try:
                    supercls_links = super().links_item  # type: ignore[misc]
                except AttributeError:  # if they aren't defined in the superclass
                    supercls_links = {}

                links = {
                    **supercls_links,
                    **self.get_model_dependency("record_links_item"),
                }
                return {k: v for k, v in links.items() if v is not None}

            @property
            def links_search_item(self) -> dict[str, Link]:
                try:
                    supercls_links = super().links_search_item  # type: ignore[misc]
                except AttributeError:  # if they aren't defined in the superclass
                    supercls_links = {}
                links = {
                    **supercls_links,
                    **self.get_model_dependency("record_search_item"),
                }
                return {k: v for k, v in links.items() if v is not None}

            @property
            def links_search(self) -> dict[str, Link]:
                try:
                    supercls_links = super().links_search  # type: ignore[misc]
                except AttributeError:  # if they aren't defined in the superclass
                    supercls_links = {}
                links = {
                    **supercls_links,
                    **pagination_endpoint_links(f"{model.blueprint_base}.search"),
                    **pagination_links_html(ui_base + "{?args*}"),
                }
                return {k: v for k, v in links.items() if v is not None}

        yield AddList("record_service_components", exists_ok=True)

        yield AddClass("RecordServiceConfig", clazz=RecordServiceConfig)
        yield AddMixins("RecordServiceConfig", ServiceConfigMixin)

        yield AddDictionary(
            "record_search_item",
            {
                "self": RecordEndpointLink(
                    f"{model.blueprint_base}.read",
                    when=has_permission("read"),
                ),
                "self_html": RecordLink(ui_url, when=has_permission("read")),
            },
        )

        yield AddDictionary(
            "record_links_item",
            {
                "self": RecordEndpointLink(
                    f"{model.blueprint_base}.read",
                    when=has_permission("read"),
                ),
                "self_html": RecordLink(ui_url, when=has_permission("read")),
            },
        )

        yield AddToList(
            "primary_record_service",
            lambda runtime_dependencies: (
                runtime_dependencies.get("Record"),
                runtime_dependencies.get("RecordServiceConfig").service_id,
            ),
        )
