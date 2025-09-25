#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Registration preset for UI JSON serializer in record response handlers.

This module provides a preset that registers the JSONUISerializer with the record
resource response handlers. It includes:

- RegisterJSONUISerializerPreset: A preset that adds the UI JSON serializer to the
  record_response_handlers dictionary with the appropriate content type
- Configuration for the "application/vnd.inveniordm.v1+json" media type
- Integration with Flask-Resources ResponseHandler and ETag headers
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from invenio_i18n import lazy_gettext as _
from werkzeug.local import LocalProxy

from oarepo_model.customizations import (
    AddMetadataExport,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask_resources.serializers import BaseSerializer

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RegisterJSONUISerializerPreset(Preset):
    """Preset for registering JSON UI Serializer."""

    depends_on = ("JSONUISerializer",)
    modifies = ("exports",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        runtime_deps = builder.get_runtime_dependencies()

        yield AddMetadataExport(
            code="ui_json",
            name=_("UI JSON"),
            mimetype="application/vnd.inveniordm.v1+json",
            serializer=cast(
                "BaseSerializer",
                LocalProxy(lambda: runtime_deps.get("JSONUISerializer")()),
            ),
        )
