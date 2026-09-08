#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Data type for PID-based record relations.

This module provides the PIDRelation data type for creating relationships
between records using persistent identifiers (PIDs). It extends the ObjectDataType
to handle record references with configurable keys, PID fields, and caching
mechanisms. The data type automatically generates the necessary relation
customizations for the model builder.
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any, cast, override

import marshmallow
from invenio_base.utils import obj_or_import_string

from oarepo_model.customizations.high_level.add_pid_relation import (
    ARRAY_PATH_ITEM,
    AddPIDRelation,
)
from oarepo_model.utils import import_runtime_model, walk_type_tree_path_leaf

from .collections import ObjectDataType

if TYPE_CHECKING:
    from collections.abc import Callable

    from invenio_records_resources.records.systemfields.pid import (
        PIDFieldContext,
    )

    from oarepo_model.customizations.base import Customization


class PIDRelation(ObjectDataType):
    """Relation to another record using a PID.

    Usage:
    ```yaml
    a:
        type: pid-relation
        keys:
        - id
        - metadata.title:
            type: i18nstr
        record_cls: "my_other_model.records:record" or class   (not required if pid_field is provided)
        pid_field: "my_module:pid_field_getter" or PIDField instance (not required if record_cls is provided)
        cache_key: "my_cache_key" (optional, used for caching the resolved record)
    ```
    """

    TYPE = "pid-relation"

    marshmallow_field_class = marshmallow.fields.Nested

    @override
    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
        path_suffix: str = "",
        ignored_keys: set[str] | None = None,
    ) -> Any:
        return super().get_facet(
            path, element, nested_facets, facets, path_suffix, ignored_keys={*(ignored_keys or ()), "@v"}
        )

    def _get_relation_model(self, element: dict[str, Any], must_exist: bool = False) -> str:
        """Get the model for the relation.

        The single seam every other method routes target-model resolution
        through, so subclasses that determine the target differently (e.g.
        InternalRelationDataType, which is always a self-reference) only
        need to override this one method.
        """
        model = element.get("model")
        if must_exist and model is None:
            raise KeyError("model is required")
        return cast("str", model)

    def _get_properties(  # noqa: PLR0912,C901 too many branches
        self,
        element: dict[str, Any],
        ignore_missing: bool = False,
    ) -> dict[str, Any]:
        """Get the properties for the recursive pid relation data type.

        Note: we can not introspect the target's schema at this point, so
        we return only the explicitly defined properties. There is no fallback
        to 'keyword'.
        """
        model_name = self._get_relation_model(element)
        try:
            target_properties = self._get_target_properties(element)
        except ModuleNotFoundError:
            if ignore_missing:
                target_properties = {}
            else:
                raise

        fallbacks = {
            "id": {"type": "keyword", "searchable": False},
            "@v": {"type": "keyword", "skip_marshmallow": True, "searchable": False},
        }

        ret: dict[str, Any] = {}
        for key in element["keys"]:
            if isinstance(key, str):
                prop = self._lookup_property(target_properties, key)
                if prop is None and not ignore_missing:
                    if key in fallbacks:
                        prop = fallbacks[key]
                    else:
                        if model_name is not None:
                            raise KeyError(f"Property not found: {key} in target properties of {model_name}")
                        raise KeyError(
                            f"Model name is not available, cannot determine target properties for '{key}'. "
                            "Either provide model or define the props explicitly."
                        )
                if prop is not None:
                    set_key_model(
                        ret,
                        key,
                        copy.deepcopy(prop),
                    )
            elif isinstance(key, dict):
                for k, v in key.items():
                    set_key_model(ret, k, v)
            else:
                raise TypeError(f"Invalid key type: {type(key)}")

        for k, v in fallbacks.items():
            if k not in ret:
                ret[k] = v
        return ret

    def _lookup_property(self, properties: dict[str, Any], key: str) -> dict[str, Any] | None:
        """Walk a dotted key path down a properties tree, mirroring set_key_model.

        Returns None if any segment of the path is missing, so callers can fall
        back to a default rather than failing outright (e.g. for system fields
        like "id" that are never part of the declared properties tree). Uses
        `walk_type_tree_path_leaf` which handles array-typed fields correctly
        (e.g. "authors.name" resolves properly instead of failing).
        """
        return walk_type_tree_path_leaf(properties, key)

    def _get_target_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        """Look up the already-built target model's real declarative schema tree.

        Returns a "properties"-style mapping (field name -> its declarative
        element dict, the same shape as this project's own model type dicts),
        merged from the target's record- and metadata-level schemas, so dotted
        'keys' entries like "metadata.title" can be resolved against the
        target's *real* field types (e.g. "vocabulary", "multilingual")
        instead of a hardcoded "keyword" guess.

        Returns an empty dict if the target can't be introspected this way
        (e.g. it was declared only via 'pid_field', or isn't an oarepo_model
        -built model) - callers fall back to "keyword" per key in that case.
        """
        model_name = self._get_relation_model(element)
        if not model_name:
            return {}

        imported = import_runtime_model(model_name)

        model_metadata = getattr(imported, "oarepo_model_arguments", {}).get("model_metadata")
        if model_metadata is None:
            return {}

        properties: dict[str, Any] = {}
        if model_metadata.record_type:
            record_root = model_metadata.types.get(model_metadata.record_type, {})
            properties.update(record_root.get("properties", {}))
        if model_metadata.metadata_type:
            properties["metadata"] = model_metadata.types.get(model_metadata.metadata_type, {})
        return properties

    @override
    def create_relations(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> list[Customization]:
        relation_path = self._relation_path(element, path)
        relation_name = self._relation_name(element, path)
        pid_field = self._relation_pid_field(element, path)
        cache_key = self._relation_cache_key(element, path)
        key_names = self._relation_key_names(element, path)

        relations: list[Customization] = [
            AddPIDRelation(
                name=relation_name,
                path=relation_path,
                keys=key_names,
                pid_field=pid_field,
                cache_key=cache_key,
                **element.get("relation_field_kwargs", {}),
            ),
        ]

        for prop_name, prop in self._get_properties(element).items():
            relations.extend(
                self._registry.get_type(prop).create_relations(
                    prop,
                    [*path, (prop_name, prop)],
                ),
            )

        return relations

    def _relation_path(
        self,
        element: dict[str, Any],  # noqa: ARG002
        path: list[tuple[str, dict[str, Any]]],
    ) -> list:
        """Get the relation path for the PID relation."""
        relation_path: list[str | type[ARRAY_PATH_ITEM]] = []
        for pth in path:
            if pth[0] == "": # TODO: see oarepo_model.datatypes.collections.ArrayDataType.create_relations
                relation_path.append(ARRAY_PATH_ITEM)
            else:
                relation_path.append(pth[0])
        return relation_path

    def _relation_name(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> str:
        relation_path = self._relation_path(element, path)
        return ".".join(str(k) for k in relation_path if k is not ARRAY_PATH_ITEM)

    def _relation_pid_field(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],  # noqa: ARG002
    ) -> PIDFieldContext:
        """Get the PID field from the element."""
        if "pid_field" in element:
            pidf = cast(
                "Callable[[dict[str, Any]], PIDFieldContext]",
                obj_or_import_string(element["pid_field"]),
            )
            if pidf is None or not callable(pidf):
                raise ValueError(
                    f"PID field {element['pid_field']} could not be imported.",
                )
            return pidf(element)
        if "record_cls" in element:
            rec = obj_or_import_string(element["record_cls"])
            if rec is None or not hasattr(rec, "pid"):
                raise ValueError(
                    f"Record class {element['record_cls']} does not have a 'pid' attribute.",
                )
            return rec.pid
        raise ValueError(
            f"Either 'pid_field' or 'record_cls' must be provided in {element=}",
        )

    def _relation_cache_key(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],  # noqa: ARG002
    ) -> str | None:
        return element.get("cache_key")

    def _relation_key_names(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],  # noqa: ARG002
    ) -> list[str]:
        keys = set()
        for key in element.get("keys", []):
            if isinstance(key, str):
                keys.add(key)
            elif isinstance(key, dict):
                keys.update(key.keys())
            else:
                raise TypeError(f"Invalid key type: {type(key)}")
        return list(keys)


def set_key_model(properties: dict[str, Any], key: str, value: Any) -> None: # TODO: duplicate-shaped with some of the set_data methods in lazy relations
    """Set a key-value pair in the properties dictionary."""
    parts = key.split(".")
    current = properties
    for part in parts[:-1]:
        if part not in current:
            current[part] = {
                "type": "object",
                "properties": {},
            }
        current = current[part]["properties"]
    current[parts[-1]] = value
