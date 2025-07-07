#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from collections import defaultdict
from functools import partial
from itertools import chain
from types import SimpleNamespace
from typing import Any

from .builder import InvenioModelBuilder
from .customizations import Customization
from .errors import ApplyCustomizationError
from .model import InvenioModel
from .presets import Preset
from .register import register_model


def model(
    name: str,
    presets: list[type[Preset] | list[type[Preset]] | tuple[type[Preset]]] = [],
    *,
    description: str = "",
    version: str = "0.1.0",
    configuration: dict[str, Any] | None = None,
    customizations: list[Customization] | None = None,
) -> SimpleNamespace:
    """
    Create a model with the given name, version, and presets.

    :param name: The name of the model.
    :param presets: A list of presets to apply to the model.
    :param description: A description of the model.
    :param version: The version of the model.
    :param config: Configuration for the model.
    :param customizations: Customizations for the model.
    :return: An instance of InvenioModel.
    """

    model = InvenioModel(
        name=name,
        version=version,
        description=description,
        configuration=configuration or {},
    )

    builder = InvenioModelBuilder(model)

    # get all presets
    sorted_presets: list[Preset] = []
    for preset_list_or_preset in presets:
        if not isinstance(preset_list_or_preset, (list, tuple)):
            preset_list_or_preset = [preset_list_or_preset]
        for preset_cls in preset_list_or_preset:
            preset = preset_cls()
            sorted_presets.append(preset)

    sorted_presets = sort_presets(sorted_presets)

    user_customizations = [*(customizations or [])]

    preset_idx = 0
    while preset_idx < len(sorted_presets):
        preset = sorted_presets[preset_idx]
        preset_idx += 1

        # if preset depends on something, make sure user customizations
        # for that dependency are applied
        idx = 0
        while idx < len(user_customizations):
            customization = user_customizations[idx]
            if customization.name in preset.depends_on:
                try:
                    customization.apply(builder, model)
                except Exception as e:
                    raise ApplyCustomizationError(
                        f"Error evaluating user customization {customization} while applying preset {preset}"
                    ) from e
                user_customizations.pop(idx)
            else:
                idx += 1

        build_dependencies = {
            dep: builder.build_partial(dep) for dep in preset.depends_on
        }
        # print("Applying preset:", preset.__class__.__name__)
        for customization in preset.apply(builder, model, build_dependencies):
            try:
                customization.apply(builder, model)
            except Exception as e:
                raise ApplyCustomizationError(
                    f"Error evaluating user customization {customization} while applying preset {preset}: {e}"
                ) from e

    for customization in user_customizations:
        # apply user customizations that were not handled by presets
        customization.apply(builder, model)

    # maybe replace this with a LazyNamespace if there are dependency issues
    ret = builder.build()
    run_checks(ret)
    ret.register = partial(register_model, model=model, namespace=ret)
    return ret


def run_checks(model: SimpleNamespace) -> None:
    # for each of sqlalchemy models, check if they have a valid table name
    from invenio_db import db

    for key, value in model.__dict__.items():
        if isinstance(value, type) and issubclass(value, db.Model):
            attr = getattr(value, "__tablename__", None)
            if not attr:
                raise ValueError(
                    f"Model {model.name} has a SQLAlchemy model {key} without a valid __tablename__."
                )


def sort_presets(presets: list[Preset]) -> list[Preset]:
    """
    Sort presets based on their dependencies.

    :param presets: List of presets to sort.
    :return: Sorted list of presets.
    """

    preset_provides_counts = defaultdict[str, int](lambda: 0)
    already_seen_provides_counts = defaultdict[str, int](lambda: 0)

    done: list[Preset] = []

    done_dependencies = set()
    created_dependencies = set()

    for preset in presets:
        for provide in preset.provides or []:
            preset_provides_counts[provide] += 1
        for provide in preset.modifies or []:
            preset_provides_counts[provide] += 1

    while presets:
        remaining: list[Preset] = []
        anything_resolved = False

        # First pass: collect presets that can be immediately applied
        for preset in presets:
            # has build-time dependency that is not resolved yet
            if any(dep not in done_dependencies for dep in preset.depends_on or []):
                remaining.append(preset)
                continue

            # modifies something that has not yet been created
            if any(dep not in created_dependencies for dep in preset.modifies or []):
                remaining.append(preset)
                continue

            done.append(preset)

            # add to created dependencies
            for provide in preset.provides or []:
                created_dependencies.add(provide)

            for provide in chain(preset.provides or [], preset.modifies or []):
                # add to done dependencies if it has been fully resolved
                already_seen_provides_counts[provide] += 1
                if (
                    already_seen_provides_counts[provide]
                    == preset_provides_counts[provide]
                ):
                    # If we have seen all provides of this preset, we can mark it as done
                    done_dependencies.add(provide)

            anything_resolved = True

        if not anything_resolved:
            # If nothing was resolved, we have a circular dependency or unresolved dependencies
            formatted_remaining: list[str] = []
            for preset in remaining:
                formatted_remaining.append(f"{preset}")
                formatted_remaining.append(f"    Provides: {preset.provides}")
                formatted_remaining.append(f"    Depends on: {preset.depends_on}")
                formatted_remaining.append(f"    Modifies: {preset.modifies}")
            raise RuntimeError(
                "Cannot resolve presets due to circular dependencies or unresolved dependencies:\n"
                + "\n".join(formatted_remaining)
            )
        presets = remaining

    return done
