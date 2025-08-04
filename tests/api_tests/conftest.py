#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

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
def draft_service_with_files(app):
    """Service instance."""
    return app.extensions["draft_with_files"].records_service


@pytest.fixture(scope="module")
def draft_file_service(app):
    """Service instance."""
    return app.extensions["draft_with_files"].draft_files_service


@pytest.fixture(scope="module")
def file_service(app):
    """Service instance."""
    return app.extensions["test"].files_service


@pytest.fixture
def input_data():
    """Input data (as coming from the view layer)."""
    return {
        "metadata": {"title": "Test"},
        "files": {
            "enabled": True,
        },
    }


@pytest.fixture
def input_data_with_files_disabled(input_data):
    """Input data with files disabled."""
    data = input_data.copy()
    data["files"]["enabled"] = False
    return data
