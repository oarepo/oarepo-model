from invenio_drafts_resources.records import Record as DraftRecordBase

from oarepo_model.api import model
from oarepo_model.presets.drafts import drafts_presets
from oarepo_model.presets.records_resources import records_resources_presets


def test_draft_builder():
    empty_model = model(
        name="test",
        version="1.0.0",
        presets=[records_resources_presets, drafts_presets],
    )

    assert issubclass(empty_model.Record, DraftRecordBase)
    assert empty_model.Record.parent_record_cls is empty_model.ParentRecord
