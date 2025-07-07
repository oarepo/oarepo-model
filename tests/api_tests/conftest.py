import pytest
from invenio_app.factory import create_api as _create_api


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return _create_api


@pytest.fixture(scope="module")
def test_service(app):
    """Service instance."""
    return app.extensions["test"].records_service


@pytest.fixture(scope="module")
def test_draft_service(app):
    """Service instance."""
    return app.extensions["draft_test"].records_service


@pytest.fixture(scope="module")
def file_service(app):
    """Service instance."""
    return app.extensions["test"].files_service


@pytest.fixture(scope="function")
def input_data():
    """Input data (as coming from the view layer)."""
    return {
        "metadata": {"title": "Test"},
        "files": {
            "enabled": True,
        },
    }


@pytest.fixture(scope="function")
def input_data_with_files_disabled(input_data):
    """Input data with files disabled."""
    data = input_data.copy()
    data["files"]["enabled"] = False
    return data
