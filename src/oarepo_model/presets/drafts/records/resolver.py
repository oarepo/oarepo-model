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

from typing import TYPE_CHECKING, Any, cast, override

from invenio_access.permissions import system_identity
from invenio_drafts_resources.services.records.service import RecordService
from invenio_pidstore.errors import PIDDoesNotExistError, PIDUnregistered
from sqlalchemy.exc import NoResultFound

from oarepo_model.customizations import (
    ChangeBase,
    Customization,
)
from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.records.resolver import RecordProxy, RecordResolver

if TYPE_CHECKING:
    from collections.abc import Generator

    from invenio_drafts_resources.records import Draft, Record
    from invenio_records_resources.references import RecordResolver as InvenioRecordResolver
    from invenio_records_resources.references.entity_resolvers import RecordProxy as InvenioRecordProxy

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel

# TODO: if used somewhere, get_needs is implemented in RDM but it will probably not work with workflows
class DraftRecordProxy(RecordProxy):
    """Resolver proxy for a OARepo record entity.

    Based on RDMRecordProxy, supports customizable record and draft classes.
    """

    @override
    def __init__(
        self,
        resolver: InvenioRecordResolver,
        ref_dict: dict[str, str],
        record_cls: type[Record],
        draft_cls: type[Draft],
    ):
        """Create the proxy."""
        # this should be record resolver?
        super().__init__(resolver, ref_dict, record_cls)
        self.draft_cls = draft_cls

    def _get_record(self, pid_value: str) -> Record:
        """Fetch the published record."""
        return cast("Record", self.record_cls.pid.resolve(pid_value))

    @override
    def _resolve(self) -> Record:
        """Resolve the Record from the proxy's reference dict."""
        pid_value = self._parse_ref_dict_id()

        draft = None
        try:
            draft = cast("Record", self.draft_cls.pid.resolve(pid_value, registered_only=False))
        except (PIDUnregistered, NoResultFound, PIDDoesNotExistError):
            # try checking if it is a published record before failing
            record = self._get_record(pid_value)
        else:
            # no exception raised. If published, get the published record instead
            record = draft if not draft.is_published else self._get_record(pid_value)

        return record

    def ghost_record(self, value: dict[str, Any]) -> dict[str, Any]:
        """Ghost representation of a record.

        Drafts at the moment cannot be resolved, service.read_many() is searching on
        public records, thus the `ghost_record` method will always kick in!
        Supports checking whether the record is draft without published record that the find_many method fails to find.
        """
        # TODO: important!!! read_draft with system_identity has security implications on sensitive metadata
        service = self._resolver.get_service()
        if isinstance(service, RecordService):
            try:
                draft_dict = service.read_draft(system_identity, value["id"]).to_dict()
                return self.pick_resolved_fields(system_identity, draft_dict)
            except PIDDoesNotExistError:
                return super().ghost_record(value)
        return super().ghost_record(value)


class DraftRecordResolver(RecordResolver):
    """Record resolver for OARepo records.

    Based on RDMRecordResolver, supports customizable record and draft classes.
    """

    # TODO: subclassed records_resources instead of RDM because of __init__ hardcoded
    # record_cls and draft_cls, discuss maintainability
    proxy_cls: type[DraftRecordProxy] = DraftRecordProxy  # for typing, initialized at registration

    @override
    def __init__(
        self,
        record_cls: type[Record],
        draft_cls: type[Draft],
        service_id: str,
        type_key: str,
        proxy_cls: type[DraftRecordProxy] | None = None,
    ) -> None:
        proxy_cls = proxy_cls or self.proxy_cls
        super().__init__(record_cls, service_id, type_key=type_key, proxy_cls=proxy_cls)
        self.draft_cls = draft_cls

    @override
    def _get_entity_proxy(self, ref_dict: dict[str, str]) -> InvenioRecordProxy:
        """Return a RecordProxy for the given reference dict."""
        # TODO: lint: superclass uses proxy_cls with three arguments
        return self.proxy_cls(self, ref_dict, self.record_cls, self.draft_cls)  # type: ignore[reportCallIssue]

    @override
    def matches_entity(self, entity: Any) -> bool:
        """Check if the entity is a draft or a record."""
        return isinstance(entity, (self.draft_cls, self.record_cls))


class DraftResolverPreset(Preset):
    """Preset for draft resolver."""

    modifies = ("RecordResolver",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ChangeBase(
            "RecordResolver",
            old_base_class=RecordResolver,
            new_base_class=DraftRecordResolver,
        )
