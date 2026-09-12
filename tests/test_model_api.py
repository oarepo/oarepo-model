# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from types import SimpleNamespace

import pytest
from invenio_db import db

from oarepo_model.api import model, run_checks
from oarepo_model.model import InvenioModel


def test_no_presets():
    with pytest.raises(ValueError, match="At least one preset must be provided"):
        model(
            name="empty_model",
            presets=[],
            version="1.0.0",
            types=[],
        )


def test_run_checks_accepts_valid_sqlalchemy_model():
    class OkModel(db.Model):
        __tablename__ = "run_checks_ok_model"
        id = db.Column(db.Integer, primary_key=True)

    invenio_model = InvenioModel(name="check_test", version="1.0.0", description="", configuration={})
    namespace = SimpleNamespace(OkModel=OkModel)
    run_checks(invenio_model, namespace)


def test_run_checks_error_path_names_the_model():
    class NoTableNameModel(db.Model):
        __tablename__ = "run_checks_no_tablename"
        id = db.Column(db.Integer, primary_key=True)

    NoTableNameModel.__tablename__ = None
    invenio_model = InvenioModel(name="check_test", version="1.0.0", description="", configuration={})
    namespace = SimpleNamespace(NoTableNameModel=NoTableNameModel)

    with pytest.raises(ValueError, match="Model check_test has a SQLAlchemy model NoTableNameModel"):
        run_checks(invenio_model, namespace)
