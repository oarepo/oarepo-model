#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
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
