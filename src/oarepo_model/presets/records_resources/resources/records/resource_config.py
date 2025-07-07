#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from flask_resources import (
    JSONSerializer,
    ResponseHandler,
)
from invenio_records_resources.resources.records.config import RecordResourceConfig
from invenio_records_resources.resources.records.headers import etag_headers

from oarepo_model.customizations import (
    AddClass,
    AddDictionary,
    AddMixins,
    Customization,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class RecordResourceConfigPreset(Preset):
    """
    Preset for record resource config class.
    """

    provides = ["RecordResourceConfig", "record_response_handlers"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        class RecordResourceConfigMixin:
            # Blueprint configuration
            blueprint_name = builder.model.base_name
            url_prefix = f"/{builder.model.slug}"

            # Response handling
            response_handlers = Dependency("record_response_handlers")

        yield AddClass("RecordResourceConfig", clazz=RecordResourceConfig)
        yield AddMixins("RecordResourceConfig", RecordResourceConfigMixin)

        yield AddDictionary(
            "record_response_handlers",
            {
                "application/json": ResponseHandler(
                    JSONSerializer(), headers=etag_headers
                )
            },
        )
