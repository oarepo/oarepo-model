# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""A module for defining presets for internal (same-record) model relations."""

from __future__ import annotations

from .draft_internal_relations import InternalRelationsDraftLookupPreset
from .ext import InternalRelationsFeaturePreset
from .record_internal_relations import InternalRelationsLookupPreset

internal_relations_preset = [
    InternalRelationsLookupPreset,
    InternalRelationsDraftLookupPreset,
    # feature
    InternalRelationsFeaturePreset,
]
