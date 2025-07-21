from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

import marshmallow
from invenio_base.utils import obj_or_import_string

from oarepo_model.customizations.high_level.add_pid_relation import (
    ARRAY_PATH_ITEM,
    AddPIDRelation,
)

from .collections import ObjectDataType

if TYPE_CHECKING:
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

    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        if "properties" in element:
            return element["properties"]
        ret: dict[str, Any] = {}
        for key in element["keys"]:
            if isinstance(key, str):
                set_key_model(ret, key, {"type": "keyword"})
            elif isinstance(key, dict):
                for k, v in key.items():
                    set_key_model(ret, k, v)
            else:
                raise ValueError(f"Invalid key type: {type(key)}")
        # if 'id' is not in keys, add it as a keyword field
        if "id" not in ret:
            ret["id"] = {"type": "keyword"}
        # if @v is not in keys, add it as a keyword field, set marshmallow as dump only
        if "@v" not in ret:
            ret["@v"] = {"type": "keyword", "skip_marshmallow": True}
        return ret

    @override
    def create_relations(
        self, element: dict[str, Any], path: list[tuple[str, dict[str, Any]]]
    ) -> list[Customization]:

        relation_path = self._relation_path(element, path)
        relation_name = self._relation_name(element, path)
        pid_field = self._pid_field(element, path)
        cache_key = self._cache_key(element, path)
        key_names = self._key_names(element, path)

        relations: list[Customization] = [
            AddPIDRelation(
                name=relation_name,
                path=relation_path,
                keys=key_names,
                pid_field=pid_field,
                cache_key=cache_key,
                **element.get("relation_field_kwargs", {}),
            )
        ]

        for prop_name, prop in self._get_properties(element).items():
            relations.extend(
                self._registry.get_type(prop).create_relations(
                    prop, path + [(prop_name, prop)]
                )
            )

        return relations

    def _relation_path(
        self, element: dict[str, Any], path: list[tuple[str, dict[str, Any]]]
    ) -> list:
        """Get the relation path for the PID relation."""
        relation_path = []
        for pth in path:
            if pth[0] == "":
                relation_path.append(ARRAY_PATH_ITEM)
            else:
                relation_path.append(pth[0])
        return relation_path

    def _relation_name(
        self, element: dict[str, Any], path: list[tuple[str, dict[str, Any]]]
    ) -> str:
        relation_path = self._relation_path(element, path)
        return ".".join(str(k) for k in relation_path if k is not ARRAY_PATH_ITEM)

    def _pid_field(
        self, element: dict[str, Any], path: list[tuple[str, dict[str, Any]]]
    ):
        """Get the PID field from the element."""
        if "pid_field" in element:
            return obj_or_import_string(element["pid_field"])(element)
        elif "record_cls" in element:
            return obj_or_import_string(element["record_cls"]).pid
        else:
            raise ValueError(
                "Either 'pid_field' or 'record_cls' must be provided in the pid-relation element."
            )

    def _cache_key(
        self, element: dict[str, Any], path: list[tuple[str, dict[str, Any]]]
    ) -> str | None:
        return element.get("cache_key", None)

    def _key_names(
        self, element: dict[str, Any], path: list[tuple[str, dict[str, Any]]]
    ) -> list[str]:
        keys = set()
        for key in element.get("keys", []):
            if isinstance(key, str):
                keys.add(key)
            elif isinstance(key, dict):
                keys.update(key.keys())
            else:
                raise ValueError(f"Invalid key type: {type(key)}")
        return list(keys)


def set_key_model(properties: dict[str, Any], key: str, value: Any) -> None:
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
