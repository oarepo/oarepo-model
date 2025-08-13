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
    AddMixins,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


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
        class RecordItemMixin:
            @property
            def components(self) -> list[ResultComponent]:
                return [
                    *super().components,  # type: ignore[misc]
                    *[
                        component()
                        for component in cast(
                            "list[type[ResultComponent]]",
                            dependencies.get(
                                "record_result_item_components",
                            ),
                        )
                    ],
                ]

        yield AddClass("RecordItem", clazz=RecordItem)
        yield AddMixins("RecordItem", RecordItemMixin)


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
        class RecordListMixin:
            @property
            def components(self) -> list[ResultComponent]:
                return [
                    *super().components,  # type: ignore[misc]
                    *[
                        component()
                        for component in cast(
                            "list[type[ResultComponent]]",
                            dependencies.get(
                                "record_result_list_components",
                            ),
                        )
                    ],
                ]

        yield AddClass("RecordList", clazz=RecordList)
        yield AddMixins("RecordList", RecordListMixin)
