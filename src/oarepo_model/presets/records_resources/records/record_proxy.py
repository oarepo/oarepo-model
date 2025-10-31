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

from invenio_records_resources.references.entity_resolvers.records import RecordProxy as InvenioRecordProxy
from oarepo_runtime import current_runtime

from oarepo_model.customizations import (
    AddClass,
    AddMixins,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask_principal import Identity, ItemNeed, Need
    from invenio_records_resources.references.entity_resolvers.records import RecordProxy as TInvenioRecordProxy

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel

else:
    TInvenioRecordProxy = object


class RecordProxyMixin(TInvenioRecordProxy):
    """Resolver proxy for a OARepo record entity.

    Based on RDMRecordProxy, supports customizable record and draft classes.
    """

    @override
    def pick_resolved_fields(self, identity: Identity, resolved_dict: dict[str, Any]) -> dict[str, Any]:
        """Select which fields to return when resolving the reference."""
        resolved_fields: dict[str, Any] = super().pick_resolved_fields(identity, resolved_dict)
        resolved_fields["links"] = resolved_dict.get("links", {})
        return resolved_fields

    def ghost_record(self, record: dict[str, str]) -> dict[str, Any]:
        """Ghost representation of a record.

        Drafts at the moment cannot be resolved, service.read_many() is searching on
        public records, thus the `ghost_record` method will always kick in!
        """
        return record

    def get_needs(self, ctx: Any = None) -> list[Need | ItemNeed]:
        """Enrich request with record needs.

        A user that can preview a record can also read its requests.
        """
        if ctx is None or "record_permission" not in ctx:
            return []
        record = self.resolve()
        record_service = current_runtime.get_record_service_for_record(record)

        record_permission = ctx["record_permission"]
        return record_service.config.permission_policy_cls(record_permission, record=record).needs  # type: ignore[no-any-return]


class RecordProxyPreset(Preset):
    """Preset for draft resolver."""

    provides = ("RecordProxy",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass(
            "RecordProxy",
            clazz=InvenioRecordProxy,
        )
        yield AddMixins(
            "RecordProxy",
            RecordProxyMixin,
        )
