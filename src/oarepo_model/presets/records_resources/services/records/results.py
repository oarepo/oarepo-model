from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from oarepo_runtime.services.results import RecordItem, RecordList

from oarepo_model.customizations import (
    AddClass,
    AddList,
    AddMixins,
    Customization,
)
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class RecordResultComponentsPreset(Preset):
    """
    Preset for record result item class.
    """

    provides = ["record_result_item_components", "record_result_list_components"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        build_dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        yield AddList(
            "record_result_item_components",
        )
        yield AddList(
            "record_result_list_components",
        )


class RecordResultItemPreset(Preset):
    """
    Preset for record result item class.
    """

    depends_on = ["record_result_item_components"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        build_dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        class RecordItemMixin:

            @property
            def components(self):
                return [
                    *super().components,
                    *[
                        component(RecordItemMixin, self)
                        for component in build_dependencies.get(
                            "record_result_item_components"
                        )
                    ],
                ]

        yield AddClass("RecordItem", clazz=RecordItem)
        yield AddMixins("RecordItem", RecordItemMixin)


class RecordResultListPreset(Preset):
    """
    Preset for record result list class.
    """

    depends_on = ["record_result_list_components"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        build_dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        class RecordListMixin:

            @property
            def components(self):
                return [
                    *super(RecordListMixin, self).components,
                    *[
                        component()
                        for component in build_dependencies.get(
                            "record_result_list_components"
                        )
                    ],
                ]

        yield AddClass("RecordList", clazz=RecordList)
        yield AddMixins("RecordList", RecordListMixin)
