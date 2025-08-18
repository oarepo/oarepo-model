#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for adding file support to record metadata.

This module provides a preset that extends RecordMetadata with file handling capabilities
by adding a bucket_id foreign key and bucket relationship to the Bucket model from
invenio_files_rest. This enables records to have associated file storage.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from invenio_db import db
from invenio_files_rest.models import Bucket
from sqlalchemy.orm import declared_attr
from sqlalchemy_utils.types import UUIDType

from oarepo_model.customizations import (
    AddClassField,
    Customization,
)
from oarepo_model.presets import Preset
from oarepo_model.presets.sqlalchemy import bucket

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.orm.decl_api import _DeclaredAttrDecorated

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordMetadataWithFilesPreset(Preset):
    """Preset for extending RecordMetadata with file support."""

    modifies = ("RecordMetadata",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClassField("RecordMetadata", "bucket_id", db.Column(UUIDType, db.ForeignKey(Bucket.id)))
        yield AddClassField(
            "RecordMetadata",
            "bucket",
            declared_attr(cast("_DeclaredAttrDecorated", bucket)),
        )
