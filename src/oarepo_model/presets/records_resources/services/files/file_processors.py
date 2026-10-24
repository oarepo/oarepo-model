# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Load file processor implementations from registered entry points."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from invenio_records_resources.services.files.processors.base import FileProcessor

from invenio_base.utils import entry_points


def get_file_processors() -> list[FileProcessor]:
    """Load and return registered file processors in entry point name order.

    Each ``oarepo.file_processors`` entry point is loaded and instantiated.
    Sorting by entry point name makes the returned order deterministic.
    """
    return [ep.load()() for ep in sorted(entry_points(group="oarepo.file_processors"), key=lambda ep: ep.name)]
