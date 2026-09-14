# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Records Models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invenio_db import db
from invenio_files_rest.models import ObjectVersion
from sqlalchemy.dialects import mysql
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy_utils.types import UUIDType

if TYPE_CHECKING:
    from sqlalchemy import Column
    from sqlalchemy.orm import Mapped


class FileRecordModelMixin:
    """Base class for a record file, storing its state and metadata."""

    __record_model_cls__ = None
    """Record model to be used for the ``record_id`` foreign key, must be set in subclasses."""

    key = db.Column(
        db.Text().with_variant(mysql.VARCHAR(255), "mysql"),
        nullable=False,
    )
    """Filename key (can be path-like also)."""

    @declared_attr
    def record_id(cls) -> Column[UUIDType]:
        """Record ID foreign key."""
        if cls.__record_model_cls__ is None:
            raise NotImplementedError(
                "FileRecordModelMixin requires __record_model_cls__ to be set in subclasses.",
            )
        return db.Column(
            UUIDType,
            db.ForeignKey(cls.__record_model_cls__.id, ondelete="RESTRICT"),
            nullable=False,
            # index=True, -- removed from here due to sqlalchemy bug
        )

    @declared_attr
    def record(cls) -> Mapped[Any]:
        """Record the file belongs to."""
        return relationship(cls.__record_model_cls__)

    @declared_attr
    def object_version_id(cls) -> Column[UUIDType]:
        """Object version ID foreign key."""
        return db.Column(
            UUIDType,
            db.ForeignKey(ObjectVersion.version_id, ondelete="RESTRICT"),
            nullable=True,
            # index=True, -- removed from here due to sqlalchemy bug
        )

    @declared_attr
    def object_version(cls) -> Mapped[ObjectVersion]:
        """Object version connected to the record file."""
        return relationship(ObjectVersion)
