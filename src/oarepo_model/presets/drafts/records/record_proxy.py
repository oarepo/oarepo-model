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
from invenio_pidstore.errors import PIDDoesNotExistError, PIDUnregistered
from invenio_rdm_records.requests.entity_resolvers import RDMRecordProxy
from invenio_records_resources.references.entity_resolvers import RecordProxy as InvenioRecordProxy
from sqlalchemy.exc import NoResultFound

from oarepo_model.customizations import (
    ChangeBase,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from invenio_drafts_resources.records.api import Record

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel
    from oarepo_model.presets.drafts.records.record_resolver import DraftRecordResolver


class DraftRecordProxy(RDMRecordProxy):
    """Resolver proxy for a OARepo record entity.

    Based on RDMRecordProxy, supports customizable record and draft classes.
    """

    def _get_record(self, pid_value: str) -> Record:
        return cast("DraftRecordResolver", self._resolver).service.record_cls.pid.resolve(pid_value)

    def _resolve(self) -> Record:
        pid_value = self._parse_ref_dict_id()

        draft = None
        try:
            draft = cast("DraftRecordResolver", self._resolver).service.draft_cls.pid.resolve(
                pid_value, registered_only=False
            )
        except (PIDUnregistered, NoResultFound, PIDDoesNotExistError):
            # try checking if it is a published record before failing
            record = self._get_record(pid_value)
        else:
            # no exception raised. If published, get the published record instead
            record = draft if not draft.is_published else self._get_record(pid_value)

        return record

    def ghost_record(self, record: dict[str, str]) -> dict[str, Any]:
        """Ghost representation of a record.

        Drafts at the moment cannot be resolved, service.read_many() is searching on
        public records, thus the `ghost_record` method will always kick in!
        Supports checking whether the record is draft without published record that the find_many method fails to find.
        """
        # TODO: important!!! read_draft with system_identity has security implications on sensitive metadata

        service = cast("DraftRecordResolver", self._resolver).service
        try:
            draft_dict = service.read_draft(system_identity, record["id"]).to_dict()
            return self.pick_resolved_fields(system_identity, draft_dict)  # type: ignore[no-any-return]
        except PIDDoesNotExistError:
            return super().ghost_record(record)  # type: ignore[no-any-return]


class DraftRecordProxyPreset(Preset):
    """Preset for draft resolver."""

    modifies = ("RecordProxy",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield ChangeBase(
            "RecordProxy",
            old_base_class=InvenioRecordProxy,
            new_base_class=DraftRecordProxy,
        )
