#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""High-level API for OARepo model creation and management.

This module provides the main entry point for creating and managing OARepo models.
It includes functions for model creation, customization application, and model
registration with the Invenio framework.
"""

from __future__ import annotations

import itertools
from functools import partial
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import SimpleNamespace

    from .customizations import Customization
    from .presets import Preset

from invenio_db import db

from .builder import InvenioModelBuilder
from .datatypes.registry import DataTypeRegistry
from .errors import ApplyCustomizationError
from .model import InvenioModel
from .register import register_model, unregister_model
from .sorter import sort_presets


def model(  # noqa: PLR0913 too many arguments
    name: str,
    presets: (list[type[Preset] | list[type[Preset]] | tuple[type[Preset]]] | None) = None,
    *,
    description: str = "",
    version: str = "0.1.0",
    configuration: dict[str, Any] | None = None,
    customizations: list[Customization] | None = None,
    types: list[dict[str, Any] | Callable[[], dict]] | None = None,
    metadata_type: str | None = None,
    record_type: str | None = None,
) -> SimpleNamespace:
    """Create a model with the given name, version, and presets.

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
        metadata_type=metadata_type,
        record_type=record_type,
    )

    type_registry = populate_type_registry(types)

    builder = InvenioModelBuilder(model, type_registry)

    # flatten and instantiate all presets
    sorted_presets = flatten_presets(presets)

    # filter out presets that do not have only_if condition satisfied
    sorted_presets = filter_only_if(sorted_presets)

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
                        f"Error evaluating user customization {customization} while applying preset {preset}",
                    ) from e
                user_customizations.pop(idx)
            else:
                idx += 1

        build_dependencies = {dep: builder.build_partial(dep) for dep in preset.depends_on}
        for customization in preset.apply(builder, model, build_dependencies):
            try:
                customization.apply(builder, model)
            except Exception as e:
                raise ApplyCustomizationError(
                    f"Error evaluating user customization {customization} while applying preset {preset}: {e}",
                ) from e

    for customization in user_customizations:
        # apply user customizations that were not handled by presets
        customization.apply(builder, model)

    # maybe replace this with a LazyNamespace if there are dependency issues
    ret = builder.build()
    run_checks(ret)
    ret.register = partial(register_model, model=model, namespace=ret)
    ret.unregister = partial(unregister_model, model=model)
    ret.get_resources = partial(get_model_resources, model=model, namespace=ret)
    return ret


def get_model_resources(model: InvenioModel, namespace: SimpleNamespace) -> dict[str, str]:
    """Get the model resources from the namespace.

    Return dictionary where key is file path which starts with
    in_memory_package_name (e.g. runtime_model_test/mappings/...) and value is the file content.
    """
    files = namespace.__files__
    return {f"{model.in_memory_package_name}/{file_name}": file_content for file_name, file_content in files.items()}


def populate_type_registry(
    types: list[dict[str, Any] | Callable[[], dict]] | None,
) -> DataTypeRegistry:
    """Populate the type registry with types from entry points or provided collections."""
    type_registry = DataTypeRegistry()
    type_registry.load_entry_points()
    if types:
        for type_collection in types:
            if isinstance(type_collection, dict):
                type_registry.add_types(type_collection)
            elif callable(type_collection):
                loaded = type_collection()
                type_registry.add_types(loaded)
            else:
                raise TypeError(
                    f"Invalid type collection: {type_collection}. Expected a dict, str to a file or Path to the file.",
                )

    return type_registry


def flatten_presets(
    presets: list[type[Preset] | list[type[Preset]] | tuple[type[Preset]]] | None,
) -> list[Preset]:
    """Flatten a list of presets into a single list of Preset instances."""
    flattened_presets: list[Preset] = []
    for p in presets or []:
        preset_list_or_preset = p
        if not isinstance(preset_list_or_preset, (list, tuple)):
            preset_list_or_preset = [preset_list_or_preset]
        for preset_cls in preset_list_or_preset:
            preset = preset_cls()
            flattened_presets.append(preset)
    return flattened_presets


def run_checks(model: SimpleNamespace) -> None:
    """Run checks on the model to ensure it is valid."""
    # for each of sqlalchemy models, check if they have a valid table name

    for key, value in model.__dict__.items():
        if isinstance(value, type) and issubclass(value, db.Model):
            attr = getattr(value, "__tablename__", None)
            if not attr:
                raise ValueError(
                    f"Model {model.name} has a SQLAlchemy model {key} without a valid __tablename__.",
                )


def filter_only_if(presets: list[Preset]) -> list[Preset]:
    """Filter presets based on their only_if condition."""
    # if there is no only_if, we can return all presets
    if not any(p.only_if for p in presets):
        return presets

    # otherwise get all provided dependencies
    all_provides = set(itertools.chain.from_iterable(p.provides for p in presets))

    # and return only those presets that do not have only_if or have all dependencies satisfied
    # by the provided dependencies
    return [p for p in presets if not p.only_if or all(d in all_provides for d in p.only_if)]
