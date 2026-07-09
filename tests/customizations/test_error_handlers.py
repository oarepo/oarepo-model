#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invenio_records_resources.services.errors import PermissionDeniedError
from oarepo_runtime.errors import AuthExceptionGroup

from oarepo_model.api import model
from oarepo_model.customizations import AddToDictionary
from oarepo_model.presets.records_resources import records_resources_preset

if TYPE_CHECKING:
    from types import SimpleNamespace

    from oarepo_model.customizations import Customization


class MyError(Exception):
    """Dummy error, only ever used as an error handler key."""


def my_handler(error: Exception) -> tuple[dict[str, Any], int]:
    """Return a canned error response."""
    return {"message": "boom"}, 418


def build_model(name: str, *customizations: Customization) -> SimpleNamespace:
    """Build an unregistered model with the records_resources preset."""
    return model(
        name=name,
        version="1.0.0",
        presets=[records_resources_preset],
        customizations=list(customizations),
    )


def test_error_handlers_default_empty():
    """The preset provides an empty record_error_handlers dictionary."""
    m = build_model("eh_default")

    assert len(m.record_error_handlers) == 1
    assert next(iter(m.record_error_handlers)) == AuthExceptionGroup

    assert len(m.RecordResourceConfig().error_handlers) == 1
    assert next(iter(m.RecordResourceConfig().error_handlers)) == AuthExceptionGroup


def test_error_handlers_reach_the_resource():
    """Handlers from the config are merged into the ones registered on the blueprint.

    ``Resource.create_error_handlers`` is what flask-resources calls to register
    error handlers on the blueprint, so this asserts the dictionary is actually wired
    up rather than just being readable off the config.
    """
    m = build_model(
        "eh_wired",
        AddToDictionary("record_error_handlers", key=MyError, value=my_handler),
    )
    resource = m.RecordResource(m.RecordResourceConfig(), None)

    handlers = dict(resource.create_error_handlers())

    assert handlers[MyError] is my_handler


def test_error_handler_overrides_invenio_default():
    """A handler in the config wins over the one declared on the resource class."""
    m = build_model(
        "eh_override",
        AddToDictionary("record_error_handlers", key=PermissionDeniedError, value=my_handler),
    )
    resource = m.RecordResource(m.RecordResourceConfig(), None)

    handlers = dict(resource.create_error_handlers())

    assert handlers[PermissionDeniedError] is my_handler
    assert m.RecordResource.error_handlers[PermissionDeniedError] is not my_handler
