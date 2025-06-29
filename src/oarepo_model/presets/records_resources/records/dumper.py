from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from oarepo_runtime.records.dumpers import SearchDumper

from oarepo_model.customizations import AddClass, AddClassList, AddMixins, Customization
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class RecordDumperPreset(Preset):
    """
    Preset for record dumper class.
    """

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        class RecordDumperMixin:
            extensions = Dependency(
                "record_dumper_extensions",
                default=[],
                transform=lambda extensions: [ext() for ext in extensions],
            )

        yield AddClass("RecordDumper", clazz=SearchDumper)
        yield AddMixins("RecordDumper", RecordDumperMixin)
        yield AddClassList("record_dumper_extensions")
