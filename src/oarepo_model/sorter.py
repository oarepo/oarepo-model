import logging
from collections import defaultdict
from graphlib import TopologicalSorter

from .presets.base import Preset

log = logging.getLogger("oarepo_model")


def sort_presets(presets: list[Preset]) -> list[Preset]:
    """
    Sort presets by their dependencies and provides attributes.
    """

    # graph is an oriented graph from a node to on which nodes it depends
    graph: dict[int, set[int]] = {id(preset): set() for preset in presets}
    presets_by_id = {id(preset): preset for preset in presets}

    provided_targets: dict[str, Preset] = {}
    provided_and_modified = defaultdict(list)

    for preset in presets:
        for provided in preset.provides:
            if provided in provided_targets:
                raise ValueError(
                    f"Preset {preset} provides {provided}, but it is already provided by {provided_targets[provided]}."
                )
            provided_targets[provided] = preset
            provided_and_modified[provided].append(preset)

    for preset in presets:
        for modified in preset.modifies:
            if modified not in provided_targets:
                raise ValueError(
                    f"Preset {preset} modifies {modified}, but it is not provided by any preset."
                )
            provided_and_modified[modified].append(preset)

    # add direct dependencies via depends_on and modifies
    for preset in presets:
        for dependency in preset.depends_on:
            # depends on must be always after all modifications
            if dependency not in provided_and_modified:
                raise ValueError(
                    f"Preset {preset} depends on {dependency}, but it is not provided by any preset."
                )
            for target in provided_and_modified[dependency]:
                graph[id(preset)].add(id(target))

    # add indirect dependencies via provided_and_modified - create chain so that the order
    # of modifications is preserved
    for provided, targets in provided_and_modified.items():
        prev = targets[0]
        for target in targets[1:]:
            graph[id(target)].add(id(prev))
            prev = target

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
            log.debug(f"{p.__class__.__name__:30s} - {", ".join(dump_str)}")
            if p.depends_on:
                log.debug(f"{'':30s} - depends on: {', '.join(p.depends_on)}")
    return sorted_presets
