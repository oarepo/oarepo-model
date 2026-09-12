# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Resource configuration preset for records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, cast, override

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
    from collections.abc import Callable, Generator

    from oarepo_runtime.api import Export, Import

    from oarepo_model.builder import InvenioModelBuilder


class _Coded(Protocol):
    """Common shape of Export/Import — the handler cache and map keys."""

    code: str
    mimetype: str


class RecordResourceConfigPreset(Preset):
    """Preset for record resource config class."""

    provides = (
        "RecordResourceConfig",
        "record_response_handlers",
        "record_request_body_parsers",
        "record_error_handlers",
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

            error_handlers = Dependency("record_error_handlers")

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

        yield AddDictionary(
            "record_error_handlers",
            {},
        )


def _merge_with_exports(record_response_handlers: dict, exports: list[Export]) -> dict:
    """Merge exports into the record response handlers."""
    return _merge_into(
        record_response_handlers,
        exports,
        lambda export: ResponseHandler(export.serializer, headers=etag_headers),
    )


def _merge_with_imports(record_request_body_parsers: dict, imports: list[Import]) -> dict:
    """Merge imports into the record_request_body_parsers."""
    return _merge_into(
        record_request_body_parsers,
        imports,
        lambda import_option: RequestBodyParser(import_option.deserializer),
    )


def _merge_into[I: _Coded, T](
    target: dict[str, T],
    items: list[I],
    make_handler: Callable[[I], T],
) -> dict[str, T]:
    """Merge exports/imports into ``target``, keyed by ``item.mimetype``.

    The handlers are created lazily on first access and cached by ``item.code``
    so that repeated accesses do not recreate them.

    Note that the map is keyed by ``mimetype`` while the cache is keyed by
    ``code``: this assumes code and mimetype are 1:1 within one model. If they
    are not, two items with the same code but different mimetypes would share
    one cached handler.
    """
    handler_cache: dict[str, T] = {}
    for item in items:
        target[item.mimetype] = _register_lazy(handler_cache, item, make_handler)
    return target


def _register_lazy[I: _Coded, T](
    cache: dict[str, T],
    item: I,
    make: Callable[[I], T],
) -> T:
    """Register a lazily-created handler for ``item`` and return its proxy.

    The handler is created when it is first accessed and cached for future use.
    """

    def lookup_or_create() -> T:
        if item.code not in cache:
            cache[item.code] = make(item)
        return cache[item.code]

    return cast("T", LazyProxy(lookup_or_create))
