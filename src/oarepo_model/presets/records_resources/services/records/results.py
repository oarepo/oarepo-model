#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate record result item and list classes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from oarepo_runtime.services.results import RecordItem, RecordList, ResultComponent

from oarepo_model.customizations import (
    AddClass,
    AddList,
    Customization,
    PrependMixin,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_runtime.services.results import RecordItem as BaseRecordItem
    from oarepo_runtime.services.results import RecordList as BaseRecordList

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel
else:
    BaseRecordItem = object
    BaseRecordList = object


class RecordResultComponentsPreset(Preset):
    """Preset for record result item class."""

    provides = ("record_result_item_components", "record_result_list_components")

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddList(
            "record_result_item_components",
        )
        yield AddList(
            "record_result_list_components",
        )


class RecordResultItemPreset(Preset):
    """Preset for record result item class."""

    depends_on = ("record_result_item_components",)
    provides = ("RecordItem",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class RecordItemMixin(BaseRecordItem):
            @property
            def components(self) -> tuple[type[ResultComponent], ...]:
                return (
                    *super().components,
                    *cast(
                        "list[type[ResultComponent]]",
                        dependencies.get(
                            "record_result_item_components",
                        ),
                    ),
                )

            @components.setter
            def components(self, _value: tuple[type[ResultComponent], ...]) -> None:
                # needed to silence mypy error about read-only property
                raise AttributeError("can't set attribute")  # pragma: no cover

        yield AddClass("RecordItem", clazz=RecordItem)
        yield PrependMixin("RecordItem", RecordItemMixin)


class RecordResultListPreset(Preset):
    """Preset for record result list class."""

    depends_on = ("record_result_list_components",)
    provides = ("RecordList",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class RecordListMixin(BaseRecordList):
            @property
            def components(self) -> tuple[type[ResultComponent], ...]:
                return (
                    *super().components,
                    *cast(
                        "list[type[ResultComponent]]",
                        dependencies.get(
                            "record_result_list_components",
                        ),
                    ),
                )

            @components.setter
            def components(self, _value: tuple[type[ResultComponent], ...]) -> None:
                # needed to silence mypy error about read-only property
                raise AttributeError("can't set attribute")  # pragma: no cover

        yield AddClass("RecordList", clazz=RecordList)
        yield PrependMixin("RecordList", RecordListMixin)
