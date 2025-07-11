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

from invenio_drafts_resources.records import ParentRecord as InvenioParentRecord
from invenio_records.systemfields import ConstantField

from oarepo_model.customizations import (
    AddClass,
    AddMixins,
    Customization,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class ParentRecordPreset(Preset):
    """
    Preset for invenio_drafts_resources.records
    """

    provides = [
        "ParentRecord",
    ]

    depends_on = [
        "PIDField",
        "PIDProvider",
        "PIDFieldContext",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        class ParentRecordMixin:
            """Base class for parent records in the model."""

            model_cls = Dependency("ParentRecordMetadata")

            schema = ConstantField(
                "$schema",
                "local://parent-v1.0.0.json",
            )

            pid = dependencies["PIDField"](
                provider=dependencies["PIDProvider"],
                context_cls=dependencies["PIDFieldContext"],
                create=True,
                delete=True,
            )

        yield AddClass(
            "ParentRecord",
            clazz=InvenioParentRecord,
        )
        yield AddMixins(
            "ParentRecord",
            ParentRecordMixin,
        )
