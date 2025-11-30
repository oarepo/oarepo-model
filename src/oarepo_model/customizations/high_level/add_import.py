#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""High-level customization for adding metadata Imports to models.

This module provides the AddMetadataImport customization that registers an import
deserializer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_runtime.api import Import

from ..base import Customization

if TYPE_CHECKING:
    from flask_babel.speaklater import LazyString
    from flask_resources.deserializers import DeserializerMixin

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddMetadataImport(Customization):
    """Customization to add metadata import to the model."""

    modifies = ("imports",)

    def __init__(  # noqa: PLR0913  # too many arguments
        self,
        code: str,
        name: LazyString,
        mimetype: str,
        deserializer: DeserializerMixin,
        description: LazyString,
        oai_name: tuple[str, str] | None = None,
        **kwargs: Any,
    ):
        """Initialize the AddMetadataImport customization.

        :param code: Code of the import format, used to identify the import format in the URL.
        :param name: Name of the import format, human-readable.
        :param description: Description of the import format, human-readable.
        :param mimetype: MIME type of the import format.
        :param deserializer: Deserializer used to deserialize from the import format into record.
        :param oai_name: Optional tuple specifying the OAI-PMH namespace and local name of the
                 metadata element of oai-pmh xml record.
        """
        super().__init__("AddMetadataImport")
        self._code = code
        self._name = name
        self._mimetype = mimetype
        self._deserializer = deserializer
        self._description = description
        self._kwargs = kwargs
        self._oai_name = oai_name

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        imports = builder.get_list("imports")
        imports.append(
            Import(
                code=self._code,
                name=self._name,
                mimetype=self._mimetype,
                description=self._description,
                deserializer=self._deserializer,
                oai_name=self._oai_name,
            )
        )
