#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Signposting preset for records.

Allows exporting a record item with available datacite export as linkset and JSON linkset.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from flask_resources.serializers import BaseSerializer
from invenio_i18n import lazy_gettext as _
from oarepo_runtime.resources.signposting import record_dict_to_json_linkset, record_dict_to_linkset

from oarepo_model.customizations import AddList, AddMetadataExport, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class LinksetSignpostingSerializer(BaseSerializer):
    """Linkset serializer serializing record item to linkset."""

    def serialize_object(self, obj: dict) -> str | Any:
        """Serialize a single record item dict to a linkset. Record item is expected to have datacite export."""
        """Serialize a single object according to the response ctx."""
        return record_dict_to_linkset(obj)

    def serialize_object_list(self, obj_list: list) -> bool:
        """Serialize a list of objects according to the response ctx."""
        raise NotImplementedError  # pragma: no cover


class JSONLinksetSignpostingSerializer(BaseSerializer):
    """Linkset serializer serializing record item to JSON linkset."""

    def serialize_object(self, obj: dict) -> dict[str, list[dict[str, Any]]] | Any:
        """Serialize a single record item dict to a JSON linkset. Record item is expected to have datacite export."""
        return record_dict_to_json_linkset(obj)

    def serialize_object_list(self, obj_list: list) -> bool:
        """Serialize a list of objects according to the response ctx."""
        raise NotImplementedError  # pragma: no cover


class SignpostingPreset(Preset):
    """Preset for record signposting exports (linkset and JSON linkset)."""

    provides = ("signposting",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddList(
            "signposting",
        )
        yield AddMetadataExport(
            code="lset",
            name=_("linkset"),
            mimetype="application/linkset",
            serializer=LinksetSignpostingSerializer(),
            display=True,
            oai_metadata_prefix=None,
            oai_schema=None,
            oai_namespace=None,
        )
        yield AddMetadataExport(
            code="jsonlset",
            name=_("JSON linkset"),
            mimetype="application/linkset+json",
            serializer=JSONLinksetSignpostingSerializer(),
            display=True,
            oai_metadata_prefix=None,
            oai_schema=None,
            oai_namespace=None,
        )
