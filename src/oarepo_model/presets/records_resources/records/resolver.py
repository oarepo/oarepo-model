#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module providing preset for draft entity resolver creation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.references import RecordResolver as invenioRecordResolver
from invenio_records_resources.references.entity_resolvers.records import RecordProxy as InvenioRecordProxy

from oarepo_model.customizations import (
    AddClass,
    AddMixins,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask_principal import Identity
    from invenio_drafts_resources.records import Record

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


def set_field(result: dict[str, Any], resolved_dict: dict[str, Any], field_name: str) -> None:
    """Set field from resolved dict to result dict."""
    from_metadata = resolved_dict.get("metadata", {}).get(field_name)
    from_data = resolved_dict.get(field_name)

    if from_metadata:
        result.setdefault("metadata", {})[field_name] = from_metadata
    if from_data:
        result[field_name] = from_data


# TODO: if used somewhere, get_needs is implemented in RDM but it would not work with workflows
class RecordProxy(InvenioRecordProxy):
    """Resolver proxy for a OARepo record entity.

    Based on RDMRecordProxy, supports customizable record and draft classes.
    """

    picked_fields = ("title", "creators", "contributors") # TODO: which fields do we actually want to use if any? should be configurable?

    @override
    def pick_resolved_fields(self, identity: Identity, resolved_dict: dict[str, Any]) -> dict[str, Any]:
        """Select which fields to return when resolving the reference."""
        resolved_fields: dict[str, Any] = super().pick_resolved_fields(identity, resolved_dict)
        resolved_fields["links"] = resolved_dict.get("links", {})


        for fld in self.picked_fields:
            set_field(resolved_fields, resolved_dict, fld)

        return resolved_fields

    def ghost_record(self, value: dict[str, Any]) -> dict[str, Any]:
        """Ghost representation of a record.

        Drafts at the moment cannot be resolved, service.read_many() is searching on
        public records, thus the `ghost_record` method will always kick in!
        Supports checking whether the record is draft without published record that the find_many method fails to find.
        """
        return {
            **value,
            "metadata": {
                "title": "Deleted record",
            },
        }


class RecordResolver(invenioRecordResolver):
    """Record resolver for OARepo records.

    Based on RDMRecordResolver, supports customizable record and draft classes.
    """

    proxy_cls: type[RecordProxy] = RecordProxy  # for typing, initialized at registration

    @override
    def __init__(
        self,
        record_cls: type[Record],
        service_id: str,
        type_key: str,
        proxy_cls: type[RecordProxy] | None = None,
    ) -> None:
        proxy_cls = proxy_cls or self.proxy_cls
        super().__init__(record_cls, service_id, type_key=type_key, proxy_cls=proxy_cls)


class ResolverPreset(Preset):
    """Preset for draft resolver."""

    provides = ("RecordResolver",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class ResolverMixin:
            """Mixin specifying record resolver."""

            type_id = f"{builder.model.base_name}"

        yield AddClass(
            "RecordResolver",
            clazz=RecordResolver,
        )
        yield AddMixins(
            "RecordResolver",
            ResolverMixin,
        )
