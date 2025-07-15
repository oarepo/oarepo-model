from oarepo_model.datatypes.registry import DataTypeRegistry
from oarepo_model.datatypes.strings import KeywordDataType


def test_datatype_registry():
    dt = DataTypeRegistry()
    dt.load_entry_points()
    assert "keyword" in dt.types
    assert isinstance(dt.types["keyword"], KeywordDataType)
