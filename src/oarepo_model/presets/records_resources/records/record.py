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

from invenio_records.systemfields import ConstantField
from invenio_records_resources.records.api import Record as InvenioRecord
from invenio_records_resources.records.systemfields import IndexField

from oarepo_model.customizations import (
    AddClass,
    AddMixins,
    Customization,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class RecordPreset(Preset):
    """
    Preset for records_resources.records
    """

    depends_on = [
        ("RecordMetadata"),
        ("PIDField"),
        ("PIDProvider"),
        ("PIDFieldContext"),
    ]

    provides = [
        "Record",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        class RecordMixin(InvenioRecord):
            """Base class for records in the model.
            This class extends InvenioRecord and can be customized further.
            """

            model_cls = Dependency("RecordMetadata")

            schema = ConstantField(
                "$schema",
                f"local://{builder.model.base_name}-v1.0.0.json",
            )

            index = IndexField(
                f"{builder.model.base_name}-metadata-v1.0.0",
            )

            pid = dependencies["PIDField"](
                provider=dependencies["PIDProvider"],
                context_cls=dependencies["PIDFieldContext"],
                create=True,
            )

            dumper = Dependency(
                "RecordDumper", transform=lambda RecordDumper: RecordDumper()
            )

        yield AddClass(
            "Record",
            clazz=InvenioRecord,
        )
        yield AddMixins(
            "Record",
            RecordMixin,
        )
