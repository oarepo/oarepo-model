#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
import itertools
import json
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import yaml

from .builder import InvenioModelBuilder
from .customizations import Customization
from .datatypes.registry import DataTypeRegistry
from .errors import ApplyCustomizationError
from .model import InvenioModel
from .presets import Preset
from .register import register_model, unregister_model
from .sorter import sort_presets


def from_json(file_name: str, origin: str | None = None) -> Callable[[], dict]:
    """Load custom data types from JSON files. 
    
    Supports two formats:
    - A list of objects, each with a 'name' field (converted into a dictionary keyed by 'name')
    - A dictionary of named objects directly
    
    If `origin` is provided, `file_name` is resolved relative to the directory of the origin file.
    Otherwise, it is resolved relative to the current working directory.
    
    :param file_name: Name of the JSON file containing the data type definitions.
    :param origin: Optional path to the file from which the load is being called (e.g., `__file__`), 
                   used to resolve the relative path to `file_name`.
    :return: A callable that returns a dictionary of data types when called.
    :raises TypeError: If the loaded content is neither a list nor a dictionary.
    """
    path = Path(origin).parent / file_name if origin else Path.cwd() / file_name
    def _loader() -> dict:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return { item["name"]: item for item in raw}
        elif isinstance(raw, dict):
            return raw
        else:
            raise TypeError(f"Expected dict or list, got {type(raw)}")
    return _loader    

def from_yaml(file_name: str, origin: str | None = None) -> Callable[[], dict]:
    """Load custom data types from YAML files. 
    
    Supports two formats:
    - A list of objects, each with a 'name' field (converted into a dictionary keyed by 'name')
    - A dictionary of named objects directly
    
    If `origin` is provided, `file_name` is resolved relative to the directory of the origin file.
    Otherwise, it is resolved relative to the current working directory.
    
    :param file_name: Name of the YAML file containing the data type definitions.
    :param origin: Optional path to the file from which the load is being called (e.g., `__file__`), 
                   used to resolve the relative path to `file_name`.
    :return: A callable that returns a dictionary of data types when called.
    :raises TypeError: If the loaded content is neither a list nor a dictionary.
    """
    path = Path(origin).parent / file_name if origin else Path.cwd() / file_name
    
    def _loader() -> dict:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return { item["name"]: item for item in raw }
        elif isinstance(raw, dict):
            return raw
        else:
            raise TypeError(f"Expected dict or list, got {type(raw)}")
    return _loader 

def model(
    name: str,
    presets: list[type[Preset] | list[type[Preset]] | tuple[type[Preset]]] = [],
    *,
    description: str = "",
    version: str = "0.1.0",
    configuration: dict[str, Any] | None = None,
    customizations: list[Customization] | None = None,
    types: list[dict[str, Any] | Callable[[], dict]] | None = None,
    metadata_type: str | None = None,
    record_type: str | None = None,
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
        metadata_type=metadata_type,
        record_type=record_type,
    )

    type_registry = DataTypeRegistry()
    type_registry.load_entry_points()
    if types:
        for type_collection in types:
            if isinstance(type_collection, dict):
                type_registry.add_types(type_collection)
            elif isinstance(type_collection, Callable):
                loaded = type_collection()
                type_registry.add_types(loaded)
            else:
                raise TypeError(
                    f"Invalid type collection: {type_collection}. "
                    "Expected a dict, str to a file or Path to the file."
                )

    builder = InvenioModelBuilder(model, type_registry)

    # get all presets
    sorted_presets: list[Preset] = []
    for preset_list_or_preset in presets:
        if not isinstance(preset_list_or_preset, (list, tuple)):
            preset_list_or_preset = [preset_list_or_preset]
        for preset_cls in preset_list_or_preset:
            preset = preset_cls()
            sorted_presets.append(preset)

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
    ret.unregister = partial(unregister_model, model=model, namespace=ret)
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


def filter_only_if(presets: list[Preset]) -> list[Preset]:
    # if there is no only_if, we can return all presets
    if not any(p.only_if for p in presets):
        return presets

    # otherwise get all provided dependencies
    all_provides = set(itertools.chain.from_iterable(p.provides for p in presets))

    # and return only those presets that do not have only_if or have all dependencies satisfied
    # by the provided dependencies
    return [
        p for p in presets if not p.only_if or all(d in all_provides for d in p.only_if)
    ]
