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

from oarepo_model.customizations import (
    AddClass,
    AddMixins,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask_principal import Identity
    from invenio_records_resources.references.entity_resolvers.records import RecordProxy as TInvenioRecordProxy

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel

else:
    TInvenioRecordProxy = object


class RecordProxyMixin(TInvenioRecordProxy):
    """Resolver proxy for a OARepo record entity.

    Based on RDMRecordProxy, supports customizable record and draft classes.
    """

    """
    picked_fields = (
        "title",
         "creators",
         "contributors",
     )  # TODO: which fields do we actually want to use if any? should be configurable?

     def set_field(result: dict[str, Any], resolved_dict: dict[str, Any], field_name: str) -> None:
         from_metadata = resolved_dict.get("metadata", {}).get(field_name)
         from_data = resolved_dict.get(field_name)

         if from_metadata:
             result.setdefault("metadata", {})[field_name] = from_metadata
         if from_data:
             result[field_name] = from_data

    """

    @override
    def pick_resolved_fields(self, identity: Identity, resolved_dict: dict[str, Any]) -> dict[str, Any]:
        """Select which fields to return when resolving the reference."""
        resolved_fields: dict[str, Any] = super().pick_resolved_fields(identity, resolved_dict)
        resolved_fields["links"] = resolved_dict.get("links", {})

        """
        # for fld in self.picked_fields:
        #     set_field(resolved_fields, resolved_dict, fld)
        """

        return resolved_fields


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
