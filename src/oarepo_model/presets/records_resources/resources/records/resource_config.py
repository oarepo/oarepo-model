#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Resource configuration preset for records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from babel.support import LazyProxy
from flask_resources import (
    RequestBodyParser,
    ResponseHandler,
)
from invenio_records_resources.resources.records.config import RecordResourceConfig
from invenio_records_resources.resources.records.headers import etag_headers

from oarepo_model.customizations import (
    AddClass,
    AddDictionary,
    Customization,
    PrependMixin,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_runtime.api import Export, Import

    from oarepo_model.builder import InvenioModelBuilder


class RecordResourceConfigPreset(Preset):
    """Preset for record resource config class."""

    provides = (
        "RecordResourceConfig",
        "record_response_handlers",
        "record_request_body_parsers",
    )

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class RecordResourceConfigMixin:
            # Blueprint configuration
            blueprint_name = builder.model.base_name
            url_prefix = f"/{builder.model.slug}"

            # Response handling
            response_handlers = Dependency("record_response_handlers", "exports", transform=_merge_with_exports)
            # Request handling
            request_body_parsers = Dependency("record_request_body_parsers", "imports", transform=_merge_with_imports)

        yield AddClass("RecordResourceConfig", clazz=RecordResourceConfig)
        yield PrependMixin("RecordResourceConfig", RecordResourceConfigMixin)

        yield AddDictionary(
            "record_response_handlers",
            {},
        )
        yield AddDictionary(
            "record_request_body_parsers",
            {},
        )


def _merge_with_exports(record_response_handlers: dict, exports: list[Export]) -> dict:
    """Merge exports into the record_response_handlers."""
    # we need to return lazy response handlers as well as do not recreate then with
    # every call. To do this we need to cache the created handlers.
    handler_cache: dict[str, ResponseHandler] = {}

    for export in exports:
        record_response_handlers[export.mimetype] = _register_export(handler_cache, export)
    return record_response_handlers


def _register_export(cache: dict[str, ResponseHandler], export: Export) -> ResponseHandler:
    """Register a new export and return its response handler.

    The handler is created when it is accessed first time and cached for future use.
    """

    def lookup_or_create() -> ResponseHandler:
        """Lookup or create a new response handler."""
        if export.code not in cache:
            cache[export.code] = ResponseHandler(
                export.serializer,
                headers=etag_headers,
            )
        return cache[export.code]

    return cast("ResponseHandler", LazyProxy(lookup_or_create))


def _merge_with_imports(record_request_body_parsers: dict, imports: list[Import]) -> dict:
    """Merge imports into the record_request_body_parsers."""
    # we need to return lazy request body parsers as well as do not recreate then with
    # every call. To do this we need to cache the created handlers.
    handler_cache: dict[str, RequestBodyParser] = {}

    for import_option in imports:
        record_request_body_parsers[import_option.mimetype] = _register_import(handler_cache, import_option)
    return record_request_body_parsers


def _register_import(cache: dict[str, RequestBodyParser], import_option: Import) -> RequestBodyParser:
    """Register a new import and return its request body parser.

    The handler is created when it is accessed first time and cached for future use.
    """

    def lookup_or_create() -> RequestBodyParser:
        """Lookup or create a new request body parser."""
        if import_option.code not in cache:
            cache[import_option.code] = RequestBodyParser(import_option.deserializer)
        return cache[import_option.code]

    return cast("RequestBodyParser", LazyProxy(lookup_or_create))
