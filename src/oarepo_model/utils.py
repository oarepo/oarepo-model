#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Utilities for OAREPO model."""

from __future__ import annotations

import copy
import importlib
import json
import keyword
import re
from collections.abc import Iterator, Mapping
from typing import TYPE_CHECKING, Any, cast, override

import marshmallow
from deepmerge import always_merger
from invenio_records_resources.records import Record

from .model import FileContent, JSONContent

if TYPE_CHECKING:
    from oarepo_model.model import ModelNamespace

from oarepo_model.c3linearize import LinearizationError, mro_without_class_construction


class ReadOnlyDict(Mapping):
    """An immutable, deep-copyable dict-like object for shared class-level constants.

    Used instead of types.MappingProxyType for values (e.g. a DataType's
    `mapping_type`/`jsonschema_type`, see datatypes/date.py, datatypes/strings.py)
    that are shared by reference across every field of that type and can later
    end up embedded, by reference, in a JSON tree that CopyFile (see
    customizations/copy_file.py) deep-copies. MappingProxyType itself can't be
    used for this: it can't be subclassed (CPython rejects it as a base type),
    and copy.deepcopy has no built-in support for it either - for any type it
    doesn't recognize, it falls back to pickling, and mappingproxy explicitly
    can't be pickled ("TypeError: cannot pickle 'mappingproxy' object"). This is
    a plain, subclassable Mapping instead, with __deepcopy__ implemented
    directly - the standard, documented copy.deepcopy extension point - so
    plain copy.deepcopy() just works on it (and anything embedding it),
    without touching copy's internals.

    This also matters for PatchJSONFile (see customizations/patch_json_file.py),
    which merges patches into existing file content via deepmerge's
    always_merger - deepmerge only merges recursively when both sides of a key
    are the same recognized container type (dict/list/set). Since a
    ReadOnlyDict is neither a dict nor a MutableMapping, deepmerge can never
    match it against a plain dict patch value and never attempts to merge
    "into" it (which would need item assignment and fail); it instead falls
    back to its type-conflict strategy ("override") and produces a brand new,
    independent dict for that key - so a patch touching this subtree always
    duplicates/replaces it wholesale rather than mutating this shared
    instance in place.
    """

    __slots__ = ("_data",)

    _data: dict[str, Any]

    def __init__(self, data: Mapping[str, Any]) -> None:
        """Initialize from a mapping, storing our own private copy of it."""
        self._data = dict(data)

    def __getitem__(self, key: str) -> Any:
        """Get an item by key."""
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        """Iterate over keys."""
        return iter(self._data)

    def __len__(self) -> int:
        """Return the number of items."""
        return len(self._data)

    def __repr__(self) -> str:
        """Return a debug representation."""
        return f"{self.__class__.__name__}({self._data!r})"

    def __deepcopy__(self, memo: dict[int, Any]) -> ReadOnlyDict:
        """Deep-copy by deep-copying the underlying dict into a new instance."""
        return ReadOnlyDict(copy.deepcopy(self._data, memo))


def is_mro_consistent(class_list: list[type]) -> bool:
    """Check if the MRO of the class list is consistent."""
    try:
        mro = mro_without_class_construction(class_list)
    except LinearizationError:
        return False
    # Check if our classes appear in the same order
    filtered_mro = [c for c in mro if c in class_list]
    return filtered_mro == class_list


def make_mro_consistent(class_list: list[type]) -> list[type]:
    """Make the MRO of the class list consistent.

    This function ensures that the classes in the list can be ordered in a way
    that respects the method resolution order (MRO) of Python classes while
    minimizing the number of changes to the original order.

    :param class_list: List of classes to be ordered.
    :return: A new list of classes ordered to be consistent with MRO.
    :raises TypeError: If the classes cannot be ordered in a way that respects MRO
        or if the classes are incompatible.
    """
    if not class_list:
        return []
    ret = mro_without_class_construction(class_list)
    ret = [x for x in ret if x in class_list]
    return [
        x for x in ret if not any(issubclass(y, x) for y in ret if y != x)
    ]  # keep most specific classes, discard base classes


def camel_case_split(s: str) -> list[str]:
    """Split a camel case string into a list of words."""
    return re.findall(r"([A-Z]?[a-z]+)", s)


def title_case(s: str) -> str:
    """Convert a string to title case."""
    parts = camel_case_split(s)
    return "".join(part.capitalize() for part in parts)


def convert_to_python_identifier(s: str) -> str:
    """Convert a string to a valid Python identifier.

    Replaces invalid characters with their transliteration to english words.

    :param s: The string to convert.
    :return: A valid Python identifier.
    """
    if not s:
        return "_empty_"

    if not s.isidentifier():
        ret = []
        for c in s:
            if not (c.isalnum() or c == "_"):
                ret.append(f"_{ord(c)}_")
            else:
                ret.append(c)
        s = "".join(ret)

    if keyword.iskeyword(s):
        s = f"{s}_"

    return s


class MultiFormatField(marshmallow.fields.Field):
    """A marshmallow field that has multiple internal formatting marshmallow fields.

    During serialization, it uses all the fields and returns a dictionary with
    keys as field names and values as the serialized values.
    """

    def __init__(
        self,
        subfields: dict[str, marshmallow.fields.Field],
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize the field with multiple subfields.

        :param subfields: A dictionary of field names and their corresponding marshmallow fields.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        if len(subfields) < 2:  # noqa: PLR2004   magic constant
            raise ValueError("MultiFormatField requires at least two subfields.")

        self.subfields = subfields

    @override
    def _serialize(
        self,
        value: Any,
        attr: str | None,
        obj: Any,
        **kwargs: Any,
    ) -> Any:
        if value is None:
            return None

        # otherwise return key: value dictionary
        return {
            key: field._serialize(  # noqa: SLF001 private value access
                value,
                attr,
                obj,
                **kwargs,
            )
            for key, field in self.subfields.items()
        }


def dump_to_json(obj: Any) -> str:
    """Dump an object to a JSON string."""

    def default_serializer(o: Any) -> Any:
        # covers MappingProxyType as well as any lazily-resolved mapping
        # (e.g. LazyMapping), which are only realized into a plain dict here.
        if isinstance(o, Mapping):
            return dict(o)
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")

    return json.dumps(obj, default=default_serializer)


def resolve_file_content(content: FileContent) -> str:
    """Resolve a module file's content, calling it if it is lazily produced."""
    if isinstance(content, JSONContent):
        content = content.resolve()
    return content


def import_runtime_model[R: Record = Record](model_name: str) -> ModelNamespace[R]:
    """Import a runtime model by name."""
    import_package = f"runtime_models_{model_name}"
    module = importlib.import_module(import_package)
    return cast("ModelNamespace", module)


def import_runtime_json(model_name: str, filename: str) -> dict[str, Any]:
    """Load and parse the JSON file content from the target model's namespace."""
    namespace = import_runtime_model(model_name)
    ns_links = namespace.__symlinks__
    ns_files = namespace.__files__

    if filename in ns_links:
        filename = ns_links[filename]
    file_content = ns_files[filename]
    if isinstance(file_content, JSONContent):
        return cast("dict[str, Any]", file_content.payload)
    return cast("dict[str, Any]", json.loads(file_content))


def deeply_copy_to_mutable(obj: Any) -> Any:
    """Convert an object to a dictionary. Any mappings or sequences are converted recursively."""
    if isinstance(obj, Mapping):
        return {k: deeply_copy_to_mutable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [deeply_copy_to_mutable(v) for v in obj]
    return obj


def _merged_one_of_properties(node: dict[str, Any]) -> dict[str, Any] | None:
    """Union the "properties" of a JSON Schema "oneOf" node's branches.

    A polymorphic field's JSON schema has no top-level "properties" - it is
    `{"oneOf": [...]}`, with each branch (variant) carrying its own
    "properties".

    :param node: a node that may contain a "oneOf" list.
    :return: the merged "properties" mapping across all branches that have
        one, or None if `node` has no usable "oneOf".
    """
    one_of = node.get("oneOf")
    if not isinstance(one_of, list):
        return None
    merged: dict[str, Any] = {}
    for branch in one_of:
        if isinstance(branch, dict) and isinstance(branch.get("properties"), dict):
            always_merger.merge(merged, copy.deepcopy(branch["properties"]))
    return merged


def walk_type_tree_path(root: Mapping[str, Any] | None, path: str) -> dict[str, Any] | None:
    """Descend a dotted path through a "type"/"properties"/"items"-shaped tree.

    Shared by oarepo_model's own raw declarative type trees (model_metadata.types)
    and JSON Schema documents - both use the same convention: an object node's
    children live under "properties", and an array node's single item type lives
    under "items", transparently unwrapped before continuing the walk (so a path
    segment naming an array-typed field descends straight into its item type,
    without needing an explicit "items" segment in `path`). A polymorphic node
    (JSON Schema "oneOf") has no "properties" of its own - see
    `_merged_one_of_properties` for how that's handled.

    :param root: the "properties"-style mapping (field name -> declarative node)
        to start walking from.
    :param path: a dot-separated field path, e.g. "metadata.authors". An empty
        path returns `root` itself, unchanged.
    :return: the "properties" mapping of the node reached by following `path`,
        or None if `root` isn't a mapping, or any segment along the way is
        missing or not an object/array/polymorphic node (e.g. a path that does
        not exist).
    """
    properties: Any = root
    if not isinstance(properties, dict):
        return None
    for part in path.split(".") if path else ():
        if part not in properties:
            return None
        node = properties[part]
        if not isinstance(node, dict):
            return None
        if node.get("type") == "array":
            node = node.get("items")
            if not isinstance(node, dict):
                return None
        next_properties = node.get("properties")
        if not isinstance(next_properties, dict):
            next_properties = _merged_one_of_properties(node)
        if not isinstance(next_properties, dict):
            return None
        properties = next_properties
    return cast("dict[str, Any]", properties)


def walk_type_tree_path_leaf(root: Mapping[str, Any] | None, path: str) -> dict[str, Any] | None:
    """Descend a dotted path and return the leaf node (not its properties).

    Like `walk_type_tree_path`, but returns the actual node at the end of the
    path instead of its "properties" mapping. This is useful when you want to
    retrieve a field definition (which may be a leaf with no "properties" key)
    rather than the properties of an object node.

    Uses `walk_type_tree_path` for all but the last segment to handle arrays
    correctly, then accesses the final segment directly.

    :param root: the "properties"-style mapping (field name -> declarative node)
        to start walking from.
    :param path: a dot-separated field path, e.g. "metadata.authors.name". An
        empty path returns `None` (no leaf can be determined).
    :return: the node at the end of `path`, or None if `root` isn't a mapping,
        any segment is missing, or the final segment has no value.
    """
    if not path:
        return None
    parts = path.split(".")
    if len(parts) == 1:
        # Single segment - just get from root
        node = root.get(parts[0]) if root else None
        return cast("dict[str, Any] | None", node) if isinstance(node, dict) else None
    # Multiple segments - use walk_type_tree_path for parent, then get leaf
    parent_path = ".".join(parts[:-1])
    leaf = parts[-1]
    parent_properties = walk_type_tree_path(root, parent_path)
    if parent_properties is None:
        return None
    node = parent_properties.get(leaf)
    return cast("dict[str, Any] | None", node) if isinstance(node, dict) else None

def walk_ui_model_path(root: Mapping[str, Any] | None, path: str) -> dict[str, Any] | None:
    """Descend a dotted path through a UI model's "children"/"child"-shaped tree.

    Mirrors `walk_type_tree_path`, but for oarepo_model's UI model convention:
    a node's children live under "children", and an array node's single item
    node lives under "child" (the counterpart of "items" in `walk_type_tree_path`),
    transparently unwrapped before continuing the walk.

    :param root: the "children"-style mapping (field name -> UI model node) to
        start walking from.
    :param path: a dot-separated field path, e.g. "metadata.authors". An empty
        path returns `root` itself, unchanged.
    :return: the "children" mapping of the node reached by following `path`,
        or None if `root` isn't a mapping, or any segment along the way is
        missing or not resolvable.
    """
    children: Any = root # TODO: perhaps unify (or not idk) with walk_type_tree_path
    if not isinstance(children, dict):
        return None
    for part in path.split(".") if path else ():
        if part not in children:
            return None
        node = children[part]
        if not isinstance(node, dict):
            return None
        if "child" in node:
            node = node["child"]
            if not isinstance(node, dict):
                return None
        next_children = node.get("children")
        if not isinstance(next_children, dict):
            return None
        children = next_children
    return cast("dict[str, Any]", children)
