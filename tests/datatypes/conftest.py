import pytest


@pytest.fixture
def datatype_registry():
    """Fixture to provide a datatype registry."""
    from oarepo_model.datatypes.registry import DataTypeRegistry

    registry = DataTypeRegistry()
    registry.load_entry_points()
    return registry
