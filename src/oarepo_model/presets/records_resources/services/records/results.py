# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

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


def _result_components_mixin(
    base: Any,
    components_key: str,
    dependencies: dict[str, Any],
) -> type:
    """Build a mixin that appends the model's result components to a result class."""

    class ResultComponentsMixin(base):
        @property
        def components(self) -> tuple[type[ResultComponent], ...]:
            return (
                *super().components,
                *cast(
                    "list[type[ResultComponent]]",
                    dependencies.get(
                        components_key,
                    ),
                ),
            )

        @components.setter
        def components(self, _value: tuple[type[ResultComponent], ...]) -> None:
            # needed to silence mypy error about read-only property
            raise AttributeError("can't set attribute")

    return ResultComponentsMixin


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
        yield AddClass("RecordItem", clazz=RecordItem)
        yield PrependMixin(
            "RecordItem",
            _result_components_mixin(
                BaseRecordItem,
                "record_result_item_components",
                dependencies,
            ),
        )


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
        yield AddClass("RecordList", clazz=RecordList)
        yield PrependMixin(
            "RecordList",
            _result_components_mixin(
                BaseRecordList,
                "record_result_list_components",
                dependencies,
            ),
        )
