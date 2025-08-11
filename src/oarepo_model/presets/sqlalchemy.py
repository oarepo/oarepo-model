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

from typing import TYPE_CHECKING, Protocol

from invenio_db import db
from invenio_files_rest.models import Bucket

if TYPE_CHECKING:
    import sqlalchemy.orm as sa_orm
    from sqlalchemy import Column


class ModelWithBucket(Protocol):
    """Protocol defining interface for models that contain a bucket relationship."""

    bucket_id: Column
    """Column containing the bucket ID reference"""


def bucket(cls: type[ModelWithBucket]) -> sa_orm.RelationshipProperty:
    """Create a relationship to a Bucket for the given model class.

    Args:
        cls: The model class implementing ModelWithBucket protocol

    Returns:
        SQLAlchemy relationship property for the bucket

    """
    return db.relationship(Bucket, foreign_keys=[cls.bucket_id])
