# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""A module for defining presets for model relations."""

from __future__ import annotations

from .ext import RelationsFeaturePreset
from .record_relations import RecordRelationsPreset

relations_preset = [
    RecordRelationsPreset,
    # feature
    RelationsFeaturePreset,
]
