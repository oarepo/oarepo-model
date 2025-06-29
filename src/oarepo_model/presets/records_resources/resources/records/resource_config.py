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

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        build_dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        class RecordResourceConfigMixin:
            # Blueprint configuration
            blueprint_name = builder.model.base_name
            url_prefix = f"/{builder.model.slug}"
            routes = Dependency("record_api_routes")

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

        yield AddDictionary(
            "record_api_routes",
            {
                "list": "",
                "item": "/<pid_value>",
            },
        )
