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
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_rdm_records.requests.entity_resolvers import RDMRecordProxy
from invenio_records_resources.references.entity_resolvers import RecordProxy as InvenioRecordProxy

from oarepo_model.customizations import (
    ChangeBase,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel
    from oarepo_model.presets.drafts.records.record_resolver import DraftRecordResolver


# TODO: if used somewhere, get_needs is implemented in RDM but it will probably not work with workflows
# TODO: if we are not expecting non-RDM records with drafts, _resolve can be directly inherited from RDMRecordProxy
class DraftRecordProxy(RDMRecordProxy):
    """Resolver proxy for a OARepo record entity.

    Based on RDMRecordProxy, supports customizable record and draft classes.
    """

    """
    # def _get_record(self, pid_value):
    #     return RDMRecord.pid.resolve(pid_value)
    #
    # def _resolve(self):
    #     pid_value = self._parse_ref_dict_id()
    #
    #     draft = None
    #     try:
    #         draft = RDMDraft.pid.resolve(pid_value, registered_only=False)
    #     except (PIDUnregistered, NoResultFound, PIDDoesNotExistError):
    #         # try checking if it is a published record before failing
    #         record = self._get_record(pid_value)
    #     else:
    #         # no exception raised. If published, get the published record instead
    #         record = draft if not draft.is_published else self._get_record(pid_value)
    #
    #     return record

    # def _get_record(self, pid_value: str) -> Record:
    #     return cast("Record", self.record_cls.pid.resolve(pid_value))
    #
    # @override
    # def _resolve(self) -> Record:
    #     pid_value = self._parse_ref_dict_id()
    #
    #     draft = None
    #     try:
    #         draft = cast("Record", self.draft_cls.pid.resolve(pid_value, registered_only=False))
    #     except (PIDUnregistered, NoResultFound, PIDDoesNotExistError):
    #         # try checking if it is a published record before failing
    #         record = self._get_record(pid_value)
    #     else:
    #         # no exception raised. If published, get the published record instead
    #         record = draft if not draft.is_published else self._get_record(pid_value)
    #
    #     return record
    """

    # TODO: stubs assume def ghost_record(self, record: str) -> dict[str, str]: ...
    def ghost_record(self, record: dict[str, Any]) -> dict[str, Any]:  # type: ignore[reportIncompatibleMethodOverride]
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
