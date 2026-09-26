# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for creating FileMetadata database model.

This module provides a preset that creates a FileMetadata class for storing
file metadata in the database. It includes table structure, indexes for
efficient querying, and relationships to record models through the
FileRecordModelMixin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_db import db
from invenio_records.models import RecordMetadataBase
from invenio_records_resources.records.models import FileRecordModelMixin

from oarepo_model.customizations import (
    AddBaseClass,
    AddClass,
    AddClassField,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


def file_metadata_preset(name: str, *, table_suffix: str, record_model_cls_name: str) -> type[Preset]:
    """Build a Preset that creates a file metadata DB model class.

    ``FileMetadataPreset``, ``FileDraftMetadataPreset``, ``MediaFileMetadataPreset`` and
    ``MediaFileDraftMetadataPreset`` are otherwise identical: each creates a
    ``db.Model``/``RecordMetadataBase``/``FileRecordModelMixin`` class whose only per-role
    difference is its table name suffix and which parent record/draft metadata model
    (``__record_model_cls__``) it belongs to.

    :param name: the partial name to create, e.g. "FileMetadata" or "MediaFileDraftMetadata".
    :param table_suffix: appended to the model's base name to form ``__tablename__``,
        e.g. "_files" or "_draft_media_files".
    :param record_model_cls_name: partial name of the parent record/draft metadata DB model
        class, e.g. "RecordMetadata" or "DraftMetadata".
    """

    class FileMetadataPreset(Preset):
        provides = (name,)

        depends_on = (
            # need to have this dependency because of __record_model_cls__ attribute
            record_model_cls_name,
        )

        @override
        def apply(
            self,
            builder: InvenioModelBuilder,
            model: InvenioModel,
            dependencies: dict[str, Any],
        ) -> Generator[Customization]:
            yield AddClass(name)
            yield AddClassField(name, "__tablename__", f"{builder.model.base_name}{table_suffix}")
            yield AddClassField(name, "__record_model_cls__", dependencies.get(record_model_cls_name))
            yield AddBaseClass(name, db.Model)
            yield AddBaseClass(name, RecordMetadataBase)
            yield AddBaseClass(name, FileRecordModelMixin)

    FileMetadataPreset.__name__ = FileMetadataPreset.__qualname__ = f"{name}Preset"
    FileMetadataPreset.__doc__ = f'Preset for creating the "{name}" file metadata DB model class.'
    return FileMetadataPreset


FileMetadataPreset = file_metadata_preset(
    "FileMetadata",
    table_suffix="_files",
    record_model_cls_name="RecordMetadata",
)
