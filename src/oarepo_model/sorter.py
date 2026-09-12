# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Sorter for presets in the Oarepo model.

This module provides functionality to sort presets based on their dependencies.
It uses a topological sorting algorithm to ensure that presets are ordered correctly
according to their dependencies and tries to perform minimal changes.
"""

from __future__ import annotations

import logging
import warnings
from collections import defaultdict
from graphlib import TopologicalSorter
from typing import TYPE_CHECKING

from .errors import PresetDeclarationWarning

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .presets.base import Preset

log = logging.getLogger("oarepo_model")

#: appended to every declaration warning so the reader knows the grace period is temporary
_DECLARATION_FIX_HINT = (
    "Fix the preset's provides/modifies; this will be treated as an error in a future version of oarepo-model."
)


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

    if log.isEnabledFor(logging.DEBUG):  # pragma: no cover
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

    # the provider of each partial always comes first in the chain, whatever
    # its position in the preset list, so that modifiers run after it
    for provided, provider in provided_targets.items():
        provided_and_modified[provided].append(provider)

    for preset in presets:
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


def check_preset_declarations(
    presets: Sequence[Preset],
    created_by: dict[str, Preset],
    touched_by: dict[str, set[Preset]],
) -> None:
    """Warn about presets whose provides/modifies do not match what they really did.

    Partial names cannot be enumerated (third-party presets invent their own), so this compares
    the declarations against what the build actually created and used. Only missing declarations
    raise :class:`~oarepo_model.errors.PresetDeclarationWarning`: they leave the build order of
    the two presets to chance, make other presets unable to declare the partial at all, and
    silently skip only_if presets. Declaring more than a given model happens to use is a harmless
    extra ordering edge, and is normal for presets that modify conditionally, so those are logged
    for debugging only.
    """
    provided = {name for preset in presets for name in preset.provides}

    # names that exist but belong to nobody: with `exists_ok` more than one preset may create
    # them, so the creator alone is not a stable owner and is only reported as the culprit.
    for name, creator in created_by.items():
        if name not in provided:
            warnings.warn(
                f"Preset {creator} creates partial '{name}', but no preset provides it, so no "
                f"other preset can declare it in modifies and only_if presets waiting for it are "
                f"skipped. {_DECLARATION_FIX_HINT}",
                PresetDeclarationWarning,
                stacklevel=2,
            )

    for preset in presets:
        created = {name for name, creator in created_by.items() if creator is preset}
        touched = {name for name, users in touched_by.items() if preset in users}
        # depends_on counts as a declaration on purpose: it orders the preset after every declared
        # modifier of the partial, which is what a preset that reads its final value needs, and such
        # a preset cannot also declare modifies - that would add a self-edge in the sorter.
        declared = {*preset.provides, *preset.modifies, *preset.depends_on}

        for name in sorted(touched - declared):
            warnings.warn(
                f"Preset {preset} uses partial '{name}', but does not declare it in modifies, so "
                f"the build order of the two is left to chance. {_DECLARATION_FIX_HINT}",
                PresetDeclarationWarning,
                stacklevel=2,
            )

        for provided in preset.provides:
            if provided not in created:
                creator = created_by.get(provided)
                who = f"it is created by {creator}" if creator else "no preset in this model creates it"
                log.debug(
                    "Preset %s provides '%s', but does not create it (%s).",
                    preset,
                    provided,
                    who,
                )

        for modified in preset.modifies:
            if modified not in created and modified not in touched:
                users = ", ".join(str(user) for user in sorted(touched_by.get(modified, ()), key=str))
                who = f"it is used by {users}" if users else "nobody uses it"
                log.debug(
                    "Preset %s declares that it modifies '%s', but never touches it (%s).",
                    preset,
                    modified,
                    who,
                )
