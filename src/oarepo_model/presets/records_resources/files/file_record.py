# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset for creating FileRecord API class.

This module provides a preset that creates a FileRecord class based on
Invenio's FileRecord API. The FileRecord represents individual files
attached to records and provides methods for file manipulation and metadata access.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.records.api import FileRecord as InvenioFileRecord

from oarepo_model.customizations import (
    AddClass,
    Customization,
    PrependMixin,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder


def file_record_preset(name: str, *, model_cls_name: str, record_cls_name: str) -> type[Preset]:
    """Build a Preset that creates a FileRecord-derived API class.

    ``FileRecordPreset``, ``FileDraftPreset``, ``MediaFileRecordPreset`` and
    ``MediaFileDraftPreset`` are otherwise identical: each adds an
    ``InvenioFileRecord`` subclass whose only per-role difference is which
    ``FileMetadata``-like DB model (``model_cls``) and which parent
    record/draft (``record_cls``) it is bound to.

    :param name: the partial name to create, e.g. "FileRecord" or "MediaFileDraft".
    :param model_cls_name: partial name of the DB model class holding this file's metadata,
        e.g. "FileMetadata" or "MediaFileDraftMetadata".
    :param record_cls_name: partial name of the parent record/draft class this file belongs
        to, e.g. "Record" or "DraftMediaFiles".
    """

    class FileRecordMixin:
        """Mixin for the file record."""

        model_cls = Dependency(model_cls_name)
        record_cls = Dependency(record_cls_name)

    class FileRecordPreset(Preset):
        provides = (name,)

        @override
        def apply(
            self,
            builder: InvenioModelBuilder,
            model: InvenioModel,
            dependencies: dict[str, Any],
        ) -> Generator[Customization]:
            yield AddClass(name, clazz=InvenioFileRecord)
            yield PrependMixin(name, FileRecordMixin)

    FileRecordPreset.__name__ = FileRecordPreset.__qualname__ = f"{name}Preset"
    FileRecordPreset.__doc__ = f'Preset for creating the "{name}" file record API class.'
    return FileRecordPreset


FileRecordPreset = file_record_preset("FileRecord", model_cls_name="FileMetadata", record_cls_name="Record")
