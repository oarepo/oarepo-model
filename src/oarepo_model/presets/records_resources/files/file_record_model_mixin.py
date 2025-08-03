#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

# Note: copied here due to a bug in sqlalchemy that causes issues with inheritance
# sqlalchemy bug https://github.com/sqlalchemy/sqlalchemy/issues/7366
# - duplicates indices in inherited models

#
# Removed all indices from here and they are re-defined in file_metadata.py
#


"""Records Models."""

from __future__ import annotations

from invenio_db import db
from invenio_files_rest.models import ObjectVersion
from sqlalchemy.dialects import mysql
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils.types import UUIDType


class FileRecordModelMixin:
    """Base class for a record file, storing its state and metadata."""

    __record_model_cls__ = None
    """Record model to be for the ``record_id`` foreign key."""

    key = db.Column(
        db.Text().with_variant(mysql.VARCHAR(255), "mysql"),
        nullable=False,
    )
    """Filename key (can be path-like also)."""

    @declared_attr
    def record_id(cls):  # noqa first argument name must be 'self'
        """Record ID foreign key."""
        return db.Column(
            UUIDType,
            db.ForeignKey(cls.__record_model_cls__.id, ondelete="RESTRICT"),
            nullable=False,
            # index=True, -- removed from here due to sqlalchemy bug
        )

    @declared_attr
    def record(cls):  # noqa first argument name must be 'self'
        """Record the file belongs to."""
        return db.relationship(cls.__record_model_cls__)

    @declared_attr
    def object_version_id(cls):  # noqa first argument name must be 'self'
        """Object version ID foreign key."""
        return db.Column(
            UUIDType,
            db.ForeignKey(ObjectVersion.version_id, ondelete="RESTRICT"),
            nullable=True,
            # index=True, -- removed from here due to sqlalchemy bug
        )

    @declared_attr
    def object_version(cls):  # noqa first argument name must be 'self'
        """Object version connected to the record file."""
        return db.relationship(ObjectVersion)
