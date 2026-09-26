# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""High-level customization for adding metadata exports to models.

This module provides the AddMetadataExport customization that registers an export
serializer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_runtime.api import Export

from ..base import Customization

if TYPE_CHECKING:
    from flask_babel.speaklater import LazyString
    from flask_resources.serializers import BaseSerializer

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddMetadataExport(Customization):
    """Customization to add metadata export to the model."""

    modifies = ("exports",)

    def __init__(  # noqa PLR0913 arguments needed in callback
        self,
        code: str,
        name: LazyString,
        mimetype: str,
        serializer: BaseSerializer,
        about_serializer: Any | None = None,
        display: bool = True,
        oai_metadata_prefix: str | None = None,
        oai_schema: str | None = None,
        oai_namespace: str | None = None,
        **kwargs: Any,
    ):
        """Initialize the AddMetadataExport customization.

        :param code: Code of the export format, used to identify the export format in the URL.
        :param name: Name of the export format, human readable.
        :param mimetype: MIME type of the export format.
        :param serializer: Serializer used to serialize the record into the export format.
        :param display: Whether the export format is displayed in the UI.
        :param oai_metadata_prefix: OAI metadata prefix, if applicable.
                    If not set, the export can not be used in OAI-PMH responses.
        :param oai_schema: OAI schema, if applicable.
                    If not set, the export can not be used in OAI-PMH responses.
        :param oai_namespace: OAI namespace, if applicable.
                    If not set, the export can not be used in OAI-PMH responses.
        """
        super().__init__(code)
        # stored as a single mapping, applied verbatim to the runtime's
        # Export dataclass in apply()
        self._options: dict[str, Any] = {
            "code": code,
            "name": name,
            "mimetype": mimetype,
            "serializer": serializer,
            "about_serializer": about_serializer,
            "display": display,
            "oai_metadata_prefix": oai_metadata_prefix,
            "oai_schema": oai_schema,
            "oai_namespace": oai_namespace,
            **kwargs,
        }

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        builder.get_list("exports").append(Export(**self._options))
