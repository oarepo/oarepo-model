# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Utils for SQLAlchemy related stuff in presets."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Protocol, cast

from invenio_db import db
from invenio_files_rest.models import Bucket

if TYPE_CHECKING:
    import uuid

    import sqlalchemy.orm as sa_orm
    from sqlalchemy import Column
    from sqlalchemy.orm.decl_api import _DeclaredAttrDecorated


class ModelWithBucket(Protocol):
    """Protocol defining interface for models that contain a bucket relationship."""

    bucket_id: ClassVar[Column[uuid.UUID]]
    """Column containing the bucket ID reference"""


class ModelWithMediaBucket(Protocol):
    """Protocol defining interface for models that contain a media bucket relationship."""

    media_bucket_id: ClassVar[Column[uuid.UUID]]
    """Column containing the media bucket ID reference"""


def bucket_func(cls: type[ModelWithBucket]) -> sa_orm.RelationshipProperty[Any]:
    """Create a relationship to a Bucket for the given model class.

    Args:
        cls: The model class implementing ModelWithBucket protocol

    Returns:
        SQLAlchemy relationship property for the bucket

    """
    return db.relationship(Bucket, foreign_keys=[cls.bucket_id])


def media_bucket_func(
    cls: type[ModelWithMediaBucket],
) -> sa_orm.RelationshipProperty[Any]:
    """Create a relationship to a Bucket for the given model class.

    Args:
        cls: The model class implementing ModelWithMediaBucket protocol

    Returns:
        SQLAlchemy relationship property for the media bucket

    """
    return db.relationship(Bucket, foreign_keys=[cls.media_bucket_id])


# not pretty
bucket = cast("_DeclaredAttrDecorated[Any]", bucket_func)
media_bucket = cast("_DeclaredAttrDecorated[Any]", media_bucket_func)
