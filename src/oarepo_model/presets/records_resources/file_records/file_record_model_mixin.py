# -*- coding: utf-8 -*-
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
    def record_id(cls):
        """Record ID foreign key."""
        return db.Column(
            UUIDType,
            db.ForeignKey(cls.__record_model_cls__.id, ondelete="RESTRICT"),
            nullable=False,
            # index=True, -- removed from here due to sqlalchemy bug
        )

    @declared_attr
    def record(cls):
        """Record the file belnogs to."""
        return db.relationship(cls.__record_model_cls__)

    @declared_attr
    def object_version_id(cls):
        """Object version ID foreign key."""
        return db.Column(
            UUIDType,
            db.ForeignKey(ObjectVersion.version_id, ondelete="RESTRICT"),
            nullable=True,
            # index=True, -- removed from here due to sqlalchemy bug
        )

    @declared_attr
    def object_version(cls):
        """Object version connected to the record file."""
        return db.relationship(ObjectVersion)

    # @declared_attr
    # def __table_args__(cls):
    #     """Table args."""
    #     return (
    #         # To make sure we don't have duplicate keys for record files
    #         db.Index(
    #             f"uidx_{cls.__tablename__}_record_id_key",
    #             "record_id",
    #             "key",
    #             unique=True,
    #         ),
    #     )
