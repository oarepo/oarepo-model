#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Sorter for presets in the Oarepo model.

This module provides functionality to sort presets based on their dependencies.
It uses a topological sorting algorithm to ensure that presets are ordered correctly
according to their dependencies and tries to perform minimal changes.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from graphlib import TopologicalSorter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .presets.base import Preset

log = logging.getLogger("oarepo_model")


def sort_presets(presets: list[Preset]) -> list[Preset]:
    """Sort presets by their dependencies and provides attributes."""
    # graph is an oriented graph from a node to on which nodes it depends
    presets_by_id = {id(preset): preset for preset in presets}

    provided_targets = _get_provided_targets(presets)
    provided_and_modified = _get_modified_targets(presets, provided_targets)

    graph = _create_preset_graph(presets, provided_and_modified)
    ts = TopologicalSorter(graph)

    sorted_preset_ids = list(ts.static_order())
    sorted_presets = [presets_by_id[preset_id] for preset_id in sorted_preset_ids]

    if log.isEnabledFor(logging.DEBUG):
        log.debug("Sorted presets:")
        for p in sorted_presets:
            dump_str = []
            if p.provides:
                dump_str.append(f"provides: {', '.join(p.provides)}")
            if p.modifies:
                dump_str.append(f"modifies: {', '.join(p.modifies)}")
            log.debug("%30s - %s", p.__class__.__name__, ", ".join(dump_str))
            if p.depends_on:
                log.debug("%30s - depends on: %s", "", ", ".join(p.depends_on))
    return sorted_presets


def _get_provided_targets(presets: list[Preset]) -> dict[str, Preset]:
    provided_targets: dict[str, Preset] = {}
    for preset in presets:
        for provided in preset.provides:
            if provided in provided_targets:
                raise ValueError(
                    f"Preset {preset} provides {provided}, but it is already provided by {provided_targets[provided]}.",
                )
            provided_targets[provided] = preset
    return provided_targets


def _get_modified_targets(
    presets: list[Preset],
    provided_targets: dict[str, Preset],
) -> dict[str, list[Preset]]:
    provided_and_modified = defaultdict(list)

    for preset in presets:
        for provided in preset.provides:
            provided_and_modified[provided].append(preset)

        for modified in preset.modifies:
            if modified not in provided_targets:
                raise ValueError(
                    f"Preset {preset} modifies {modified}, but it is not provided by any preset.",
                )
            provided_and_modified[modified].append(preset)
    return provided_and_modified


def _create_preset_graph(
    presets: list[Preset],
    provided_and_modified: dict[str, list[Preset]],
) -> dict[int, set[int]]:
    """Create a graph of presets with their dependencies."""
    graph: dict[int, set[int]] = {id(preset): set() for preset in presets}
    # add direct dependencies via depends_on and modifies
    for preset in presets:
        for dependency in preset.depends_on:
            # depends on must be always after all modifications
            if dependency not in provided_and_modified:
                raise ValueError(
                    f"Preset {preset} depends on {dependency}, but it is not provided by any preset.",
                )
            for target in provided_and_modified[dependency]:
                graph[id(preset)].add(id(target))

    # add indirect dependencies via provided_and_modified - create chain so that the order
    # of modifications is preserved
    for targets in provided_and_modified.values():
        prev = targets[0]
        for target in targets[1:]:
            graph[id(target)].add(id(prev))
            prev = target
    return graph
