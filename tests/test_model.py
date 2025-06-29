from invenio_records.systemfields.constant import ConstantField
from invenio_records_resources.records.systemfields.pid import PIDFieldContext
from invenio_records_resources.resources.records.config import RecordResourceConfig
from invenio_records_resources.resources.records.resource import (
    RecordResource,
)
from invenio_records_resources.services.records.config import RecordServiceConfig
from invenio_records_resources.services.records.service import RecordService
from oarepo_runtime.records.dumpers import SearchDumper
from oarepo_runtime.services.results import RecordItem, RecordList
from opensearch_dsl.index import Index

from oarepo_model.api import model
from oarepo_model.presets.records_resources import records_resources_presets


def test_create_default_model():
    my_model = model(
        name="test",
        version="1.0.0",
        presets=[records_resources_presets],
    )
    my_model.register()

    # record level
    assert my_model.pid_provider is not None
    record = my_model.record
    assert record is not None

    assert isinstance(record.pid, PIDFieldContext)

    assert isinstance(record.schema, ConstantField)
    assert record.schema.value == "local://test-v1.0.0.json"

    assert isinstance(record.index, Index)
    assert record.index._name == "test-metadata-v1.0.0"
    assert record.index._aliases == {}

    assert isinstance(record.dumper, SearchDumper)
    assert record.dumper.extensions == []

    # service level
    assert issubclass(my_model.record_service, RecordService)
    assert issubclass(my_model.record_service_config, RecordServiceConfig)

    assert issubclass(my_model.record_service_config.result_item_cls, RecordItem)
    assert issubclass(my_model.record_service_config.result_list_cls, RecordList)

    assert my_model.record_service_config.search is not None

    assert issubclass(my_model.record_resource, RecordResource)
    assert issubclass(my_model.record_resource_config, RecordResourceConfig)

    assert "application/json" in my_model.record_resource_config.response_handlers
    assert "list" in my_model.record_resource_config.routes
