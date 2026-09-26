# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Utils for SQLAlchemy related stuff in presets."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from invenio_db import db
from invenio_files_rest.models import Bucket

if TYPE_CHECKING:
    from collections.abc import Callable

    import sqlalchemy.orm as sa_orm
    from sqlalchemy.orm.decl_api import _DeclaredAttrDecorated


def _bucket_relationship(
    column_name: str,
) -> Callable[[type], sa_orm.RelationshipProperty[Any]]:
    """Create a declared_attr factory relating a model to its Bucket via column_name."""

    def bucket_func(cls: type) -> sa_orm.RelationshipProperty[Any]:
        """Create a relationship to a Bucket for the given model class."""
        return db.relationship(Bucket, foreign_keys=[getattr(cls, column_name)])

    return bucket_func


# not pretty
bucket = cast("_DeclaredAttrDecorated[Any]", _bucket_relationship("bucket_id"))
media_bucket = cast("_DeclaredAttrDecorated[Any]", _bucket_relationship("media_bucket_id"))
