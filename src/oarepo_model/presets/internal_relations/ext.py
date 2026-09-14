# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""A module for defining the internal-relations feature preset."""

from __future__ import annotations

from oarepo_runtime import __version__

from oarepo_model.presets.records_resources.ext import feature_preset

# Records the `oarepo_runtime` version (the package `InternalRelation`/`InternalRelations`
# actually come from) under the "internal-relations" feature key, so consumers can
# introspect whether/which version of internal relations a model has enabled via its
# `features` metadata, the same way they already can for "relations".
InternalRelationsFeaturePreset = feature_preset("internal-relations", __version__)
