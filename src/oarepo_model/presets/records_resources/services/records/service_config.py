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

from typing import TYPE_CHECKING, Any, cast, override

from invenio_records_resources.services import (
    EndpointLink,
    Link,
    LinksTemplate,
    RecordEndpointLink,
    pagination_endpoint_links,
)
from invenio_records_resources.services.records.config import (
    RecordServiceConfig,
)
from oarepo_runtime.services.config import (
    has_permission,
)

from oarepo_model.customizations import (
    AddClass,
    AddDictionary,
    AddList,
    AddToList,
    Customization,
    PrependMixin,
)
from oarepo_model.model import Dependency, InvenioModel, ModelMixin
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Mapping

    import marshmallow as ma
    from invenio_records_permissions.policies.records import RecordPermissionPolicy
    from invenio_records_resources.records.api import Record
    from invenio_records_resources.services.records.components import ServiceComponent
    from invenio_records_resources.services.records.config import (
        RecordServiceConfig as BaseRecordServiceConfig,
    )
    from invenio_records_resources.services.records.config import SearchOptions
    from invenio_records_resources.services.records.results import (
        RecordItem,
        RecordList,
    )

    from oarepo_model.builder import InvenioModelBuilder


else:
    BaseRecordServiceConfig = object


class RecordServiceConfigPreset(Preset):
    """Preset for record service config class."""

    provides = (
        "RecordServiceConfig",
        "record_service_components",
        "record_links_item",
        "record_search_item_links",
        "record_search_links",
    )

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class ServiceConfigMixin(ModelMixin, BaseRecordServiceConfig):
            result_item_cls = cast("type[RecordItem]", Dependency("RecordItem"))
            result_list_cls = cast("type[RecordList]", Dependency("RecordList"))

            url_prefix = f"/{builder.model.slug}/"

            permission_policy_cls = cast(
                "type[RecordPermissionPolicy]", Dependency("PermissionPolicy")
            )

            schema = cast("type[ma.Schema]", Dependency("RecordSchema"))

            search = cast(
                "type[SearchOptions]",
                Dependency("RecordSearchOptions", transform=lambda x: x()),
            )

            record_cls = cast("type[Record]", Dependency("Record"))

            service_id = builder.model.base_name

            indexer_queue_name = f"{builder.model.base_name}_indexer"

            search_item_links_template = LinksTemplate

            @property
            def components(self) -> tuple[type[ServiceComponent], ...]:  # type: ignore[reportIncompatibleVariableOverride]
                # TODO: needs to be fixed as we have multiple mixins and the sources
                # in oarepo-runtime do not support this yet
                # return process_service_configs(
                #     self, self.get_model_dependency("record_service_components") # noqa: ERA001
                #
                return (
                    *super().components,
                    *cast(
                        "list[type[ServiceComponent]]",
                        self.get_model_dependency("record_service_components"),
                    ),
                )

            model = builder.model.name

            @property
            def links_item(  # type: ignore[reportIncompatibleVariableOverride]
                self,
            ) -> Mapping[str, Callable[..., Link | EndpointLink] | Link | EndpointLink]:
                try:
                    supercls_links = super().links_item
                except AttributeError:  # if they aren't defined in the superclass
                    supercls_links = {}

                links = {
                    **supercls_links,
                    **self.get_model_dependency("record_links_item"),
                }
                return {k: v for k, v in links.items() if v is not None}

            @property
            def links_search_item(self) -> Mapping[str, Link]:  # type: ignore[reportIncompatibleVariableOverride]
                try:
                    # this is oarepo extension - do not put all links on search result
                    # item
                    supercls_links = super().links_search_item  # type: ignore[misc]
                except AttributeError:  # if they aren't defined in the superclass
                    supercls_links = {}
                links = {
                    **supercls_links,
                    **self.get_model_dependency("record_search_item_links"),
                }
                return {k: v for k, v in links.items() if v is not None}

            @property
            def links_search(  # type: ignore[reportIncompatibleVariableOverride]
                self,
            ) -> Mapping[str, Callable[..., Link | EndpointLink] | Link | EndpointLink]:
                try:
                    supercls_links = super().links_search
                except AttributeError:  # if they aren't defined in the superclass
                    supercls_links = {}
                links = {
                    **supercls_links,
                    **self.get_model_dependency("record_search_links"),
                }
                return {k: v for k, v in links.items() if v is not None}

        yield AddList("record_service_components", exists_ok=True)

        yield AddClass("RecordServiceConfig", clazz=RecordServiceConfig)
        yield PrependMixin("RecordServiceConfig", ServiceConfigMixin)

        yield AddDictionary(
            "record_search_item_links",
            {
                "self": RecordEndpointLink(
                    f"{model.blueprint_base}.read",
                    when=has_permission("read"),
                ),
            },
        )

        yield AddDictionary(
            "record_links_item",
            {
                "self": RecordEndpointLink(
                    f"{model.blueprint_base}.read",
                    when=has_permission("read"),
                ),
            },
        )

        yield AddDictionary(
            "record_search_links",
            pagination_endpoint_links(f"{model.blueprint_base}.search"),
        )

        yield AddToList(
            "primary_record_service",
            lambda runtime_dependencies: (
                runtime_dependencies.get("Record"),
                runtime_dependencies.get("RecordServiceConfig").service_id,
            ),
        )
