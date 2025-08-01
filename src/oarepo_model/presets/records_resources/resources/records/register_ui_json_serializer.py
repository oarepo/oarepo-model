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

from flask_resources import ResponseHandler
from invenio_records_resources.resources.records.headers import etag_headers
from werkzeug.local import LocalProxy

from oarepo_model.customizations import (
    AddToDictionary,
    Customization,
)
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder

class RegisterJSONUISerializerPreset(Preset):
    """
    Preset for registering JSON UI Serializer.
    """

    depends_on = ["JSONUISerializer"]
    modifies = ["record_response_handlers"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        
        runtime_deps = builder.get_runtime_dependencies()
        proxy = LocalProxy(lambda:ResponseHandler(
                    runtime_deps.get('JSONUISerializer')(), headers=etag_headers
                ))
        
        yield AddToDictionary(
            "record_response_handlers",
            {
                "application/vnd.inveniordm.v1+json": proxy
            },
        )