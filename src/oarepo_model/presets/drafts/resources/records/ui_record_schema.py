#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator, cast

import marshmallow
from flask_resources import BaseObjectSchema

from oarepo_model.customizations import AddClass, AddMixins, Customization
from oarepo_model.datatypes.collections import ObjectDataType
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

from invenio_rdm_records.resources.serializers.ui.fields import AccessStatusField
import marshmallow.fields as fields
from invenio_rdm_records.resources.serializers.ui.schema import FormatDate, FormatEDTF, TombstoneSchema
from oarepo_model.datatypes.boolean import FormatBoolean

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder

class DraftRecordUISchemaMixin:
    is_draft = FormatBoolean(attribute="is_draft") 
    
    
class DraftsRecordUISchemaPreset(Preset):
    """
    Preset for draft service class.
    """

    modifies = ["RecordUISchema"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        
        yield AddMixins("RecordUISchema", DraftRecordUISchemaMixin)
