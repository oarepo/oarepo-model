#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""A module for defining presets for model relations."""

from __future__ import annotations

from .ext import RelationsFeaturePreset
from .record_relations import RecordRelationsPreset

relations_preset = [
    RecordRelationsPreset,
    # feature
    RelationsFeaturePreset,
]
