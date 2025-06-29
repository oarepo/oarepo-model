from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from invenio_records_resources.resources.records.resource import RecordResource

from oarepo_model.customizations import AddClass, Customization
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class RecordResourcePreset(Preset):
    """
    Preset for record resource class.
    """

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        build_dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        yield AddClass("RecordResource", RecordResource)
