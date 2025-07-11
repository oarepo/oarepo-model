from invenio_rdm_records.records.api import RDMRecord

from oarepo_model.api import model
from oarepo_model.presets.drafts import drafts_presets
from oarepo_model.presets.rdm import rdm_presets
from oarepo_model.presets.records_resources import records_resources_presets


def test_rdm_builder():
    empty_model = model(
        name="test",
        version="1.0.0",
        presets=[records_resources_presets, drafts_presets, rdm_presets],
    )

    assert issubclass(empty_model.Record, RDMRecord)