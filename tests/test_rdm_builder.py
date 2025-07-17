from invenio_rdm_records.records.api import RDMRecord, RDMDraft
from oarepo_runtime.resources.resource import BaseRecordResource

from oarepo_model.api import model
from oarepo_model.presets.drafts import drafts_presets
from oarepo_model.presets.rdm import rdm_presets
from oarepo_model.presets.records_resources import records_resources_presets
from oarepo_runtime.services.service import SearchAllRecordsService
from invenio_rdm_records.records.api import RDMParent

def test_rdm_builder():
    empty_model = model(
        name="test",
        version="1.0.0",
        presets=[records_resources_presets, drafts_presets, rdm_presets],
        debug=True,
    )

    assert issubclass(empty_model.Record, RDMRecord)
    assert issubclass(empty_model.Draft, RDMDraft)
    assert issubclass(empty_model.ParentRecord, RDMParent)
    assert issubclass(empty_model.RecordService, SearchAllRecordsService)
    assert issubclass(empty_model.RecordResource, BaseRecordResource)
    #assert issubclass(empty_model., RDMRecord)
