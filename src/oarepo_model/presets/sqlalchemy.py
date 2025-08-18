#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Utils for SQLAlchemy related stuff in presets."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, cast

from invenio_db import db
from invenio_files_rest.models import Bucket

if TYPE_CHECKING:
    import sqlalchemy.orm as sa_orm
    from sqlalchemy import Column
    from sqlalchemy.orm.decl_api import _DeclaredAttrDecorated
    from sqlalchemy_utils.types import UUIDType


class ModelWithBucket(Protocol):
    """Protocol defining interface for models that contain a bucket relationship."""

    bucket_id: Column[UUIDType]
    """Column containing the bucket ID reference"""


class ModelWithMediaBucket(Protocol):
    """Protocol defining interface for models that contain a media bucket relationship."""

    media_bucket_id: Column[UUIDType]
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
