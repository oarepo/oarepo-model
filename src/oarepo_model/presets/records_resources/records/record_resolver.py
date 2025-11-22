#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module providing preset for draft entity resolver creation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.references import RecordResolver as invenioRecordResolver

from oarepo_model.customizations import (
    AddClass,
    Customization,
    PrependMixin,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordResolverPreset(Preset):
    """Preset for draft resolver."""

    provides = ("RecordResolver",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class ResolverMixin:
            """Mixin specifying record resolver."""

            type_id = f"{builder.model.base_name}"

        yield AddClass(
            "RecordResolver",
            clazz=invenioRecordResolver,
        )
        yield PrependMixin(
            "RecordResolver",
            ResolverMixin,
        )
