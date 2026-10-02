# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Utilities for OAREPO model."""

from __future__ import annotations

import copy
import importlib
import json
import keyword
import re
from collections.abc import Callable, Iterator, Mapping
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Literal, cast, override

import marshmallow
from deepmerge import DEFAULT_TYPE_SPECIFIC_MERGE_STRATEGIES
from deepmerge.merger import Merger
from deepmerge.strategy.core import STRATEGY_END
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
    which merges patches into existing file content via deepmerge - deepmerge
    only merges recursively when both sides of a key are the same recognized
    container type (dict/list/set). Since a ReadOnlyDict is neither a dict nor
    a MutableMapping, deepmerge can never match it against a plain dict patch
    value and never attempts to merge "into" it (which would need item
    assignment and fail); it instead falls back to its type-conflict strategy
    ("override") and produces a brand new, independent dict for that key - so
    a patch touching this subtree always duplicates/replaces it wholesale
    rather than mutating this shared instance in place. `readonly_dict_merger`
    below teaches a dedicated merger how to do this without mutating the
    ReadOnlyDict either.
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


def _resolve_readonly_dict_conflict(merger: Merger, path: list, base: Any, nxt: Any) -> Any:
    """Deep-clone a non-dict Mapping ``base`` to a plain dict, then merge."""
    if isinstance(base, Mapping) and not isinstance(base, dict) and isinstance(nxt, dict):
        # Tuples must stay tuples here: deepmerge appends two lists, so converting
        # a tuple base would turn deepmerge's override into a concatenation.
        return merger.value_strategy(path, deepcopy_to_plain(base), nxt)
    return STRATEGY_END


readonly_dict_merger = Merger(
    type_strategies=DEFAULT_TYPE_SPECIFIC_MERGE_STRATEGIES,
    fallback_strategies=["override"],
    type_conflict_strategies=[_resolve_readonly_dict_conflict, "override"],
)
"""A deepmerge ``Merger`` that also knows how to merge into a ``ReadOnlyDict``.

``deepmerge``'s ``always_merger`` (which this is otherwise identical to) only
merges two values recursively when both sides of a key are the same
recognized container type (``dict``/``list``/``set``). Since ``ReadOnlyDict``
isn't a ``dict``, it never matches that check and instead falls through to
the "override" type-conflict strategy, which replaces the *entire* value with
the patch payload - e.g. patching ``{"copy_to": "boost_10"}`` onto a title
field would wipe out its ``type``/``fields`` instead of adding ``copy_to``
alongside them (see e.g. ``PatchIndexPropertyMapping``).

This merger adds an extra type-conflict strategy: when the base side of a
conflict is a non-dict ``Mapping`` and the incoming side is a ``dict``, the
base is first deep-cloned into an equivalent plain ``dict`` tree, and merging
proceeds normally from there - the original ``ReadOnlyDict`` instance is left
untouched. It is a standalone instance (not a patched ``always_merger``), so
it must be used explicitly wherever a merge might encounter a ``ReadOnlyDict``
instead of ``deepmerge.always_merger``.
"""


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
    """Split a camel case string into a list of words, keeping acronym runs together."""
    return re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", s)


def title_case(s: str) -> str:
    """Convert a string to title case, preserving acronym runs like "PID".

    :param s: The string to convert.
    :return: A title-cased string usable as a Python identifier.
    :raises ValueError: If the string contains no characters to title case.
    """
    ret = "".join(part if part.isupper() else part[0].upper() + part[1:] for part in camel_case_split(s))
    if not ret:
        raise ValueError(f"Cannot convert {s!r} to a title case name, it contains no letters or digits.")
    if ret[0].isdigit():
        ret = f"_{ret}"
    return ret


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
        if not s.isidentifier():
            # the transliteration above only replaces characters, it cannot fix a leading digit
            s = f"_{s}"

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
        if len(subfields) < 2:  # noqa PLR2004 no need to create a constant here
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
            key: field._serialize(  # noqa SLF001 - ok to access private method here
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


def in_memory_package_name(base_name: str) -> str:
    """Return the name of the in-memory (importable) package for a model base name.

    Single source of the ``runtime_models_`` prefix - InvenioModel.in_memory_package_name
    and import_runtime_model both build on this, and generated classes carry it as
    their ``__module__`` so that dotted paths (pickle, marshmallow Nested) resolve
    to the model's own package.
    """
    return f"runtime_models_{base_name}"


def import_runtime_model[R: Record = Record](model_name: str) -> ModelNamespace[R]:
    """Import a runtime model by name."""
    module = importlib.import_module(in_memory_package_name(model_name))
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


def deepcopy_to_plain(obj: Any) -> Any:
    """Convert an object to a dictionary.

    Unlike the "deepcopy" it also converts lazy mappings to plain dicts.
    """
    if isinstance(obj, Mapping):
        return {k: deepcopy_to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [deepcopy_to_plain(v) for v in obj]
    return copy.deepcopy(obj)


def _merged_one_of_properties(node: dict[str, Any]) -> dict[str, Any] | None:
    """Union the "properties" of a JSON Schema "oneOf" node's branches.

    A polymorphic field's JSON schema has no top-level "properties" - it is
    `{"oneOf": [...]}`, with each branch (variant) carrying its own
    "properties".

    :param node: a node that may contain a "oneOf" list.
    :return: the merged "properties" mapping across all branches that have
        one
    :raises TypeError: if `oneOf` is not a list
    """
    one_of = node.get("oneOf")
    if not isinstance(one_of, list):
        raise TypeError("oneOf must be a list")
    merged: dict[str, Any] = {}
    for branch in one_of:
        if isinstance(branch, dict) and isinstance(branch.get("properties"), dict):
            readonly_dict_merger.merge(merged, copy.deepcopy(branch["properties"]))
    return merged


def _resolve_declarative_type_node(
    node: dict[str, Any],
    types: Mapping[str, Any] | None,
    _seen: frozenset[str] = frozenset(),
    _memo: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Resolve a declarative type node against the model's named-type registry.

    Two shapes only exist in the raw declarative tree (model_metadata.types),
    never in the built mapping/json schema/ui model:

    - a *named type reference* - ``{"type": "General"}`` has no inline
      "properties"; its definition lives under the same name in the model's
      types registry. The reference is merged over the referred definition
      (the same semantics the datatype registry's WrappedDataType applies).
    - a *polymorphic node* - ``{"type": "polymorphic", "oneof": [...]}``; its
      variants are resolved recursively and their "properties" unioned, as
      `create_mapping` does for the built mapping.

    Built-artifact nodes (no named refs, JSON-Schema "oneOf" with inline
    branches) pass through unchanged, so the same resolver is safe to apply
    before any walk, declarative or built.

    Copying strategy (P2-F5): the merger *mutates its destination* but never
    its sources - a referred definition is deep-copied once per type name
    (`_memo`, one per call tree) and only then merged per node; a reference
    carrying only scalar overrides (the common case) takes a shallow copy of
    that memoized definition without touching shared nested containers.
    """
    if types is None or not isinstance(node, dict):
        return node
    node = _resolve_named_type_reference(node, types, _seen, _memo)
    if node.get("type") == "polymorphic" and isinstance(node.get("oneof"), list):
        node = {**node, "properties": _merge_declarative_oneof_properties(node["oneof"], types, _seen, _memo)}
    return node


def _resolve_named_type_reference(
    node: dict[str, Any],
    types: Mapping[str, Any],
    _seen: frozenset[str],
    _memo: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    """Follow the node's named type reference through the registry, if it is one.

    See _resolve_declarative_type_node for the copy/memoization strategy.
    """
    type_name = node.get("type")
    if not isinstance(type_name, str) or type_name not in types:
        return node
    if type_name in _seen:
        raise TypeError(f"Circular named type reference: {type_name}")
    referred = types[type_name]
    if not isinstance(referred, dict):
        raise TypeError(f"Named type {type_name} must be a mapping, is {referred}")
    overrides = {k: v for k, v in node.items() if k != "type"}
    if _memo is not None:
        base = _memo.get(type_name)
        if base is None:
            base = copy.deepcopy(referred)
            _memo[type_name] = base
        if any(isinstance(v, dict | list) for v in overrides.values()):
            resolved = readonly_dict_merger.merge(copy.deepcopy(base), overrides)
        else:
            resolved = {**base, **overrides}
    else:
        resolved = readonly_dict_merger.merge(copy.deepcopy(referred), overrides)
    return _resolve_declarative_type_node(resolved, types, _seen | {type_name}, _memo)


def _merge_declarative_oneof_properties(
    oneof: list[Any],
    types: Mapping[str, Any] | None,
    _seen: frozenset[str],
    _memo: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    """Union the resolved variant properties of a declarative polymorphic node.

    Straight references are fine (nothing mutates the merged tree), but a
    nested conflict must not be merged in place - it would mutate the *first*
    branch's (possibly registry-owned) subtree the merged tree still aliases.
    """
    merged_properties: dict[str, Any] = {}
    for branch in oneof:
        if not isinstance(branch, dict):
            continue
        resolved_branch = _resolve_declarative_type_node(branch, types, _seen, _memo)
        if not isinstance(resolved_branch.get("properties"), dict):
            continue
        for prop_key, prop_value in resolved_branch["properties"].items():
            existing = merged_properties.get(prop_key)
            if isinstance(existing, dict) and isinstance(prop_value, dict):
                merged_properties[prop_key] = readonly_dict_merger.merge(
                    copy.deepcopy(existing),
                    prop_value,
                )
            else:
                merged_properties[prop_key] = prop_value
    return merged_properties


def _fully_resolve_declarative_node(
    node: dict[str, Any],
    types: Mapping[str, Any] | None,
    _seen: frozenset[str] = frozenset(),
    _memo: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Resolve a declarative node *and* every named-type reference inside its subtree.

    `_resolve_declarative_type_node` resolves only the node itself - enough for
    walking, where each descended node is resolved in turn. A leaf copied into
    *another* model (a cross-model relation's 'keys'), however, must not
    contain references the target's registry cannot resolve - so the whole
    subtree is expanded here. A genuinely cyclic named type can not be inlined
    and raises, same as cyclic walk resolution does.
    """
    if types is None or not isinstance(node, dict):
        return node
    type_name = node.get("type")
    resolved_node = _resolve_declarative_type_node(node, types, _seen, _memo)
    seen_now = _seen | {type_name} if isinstance(type_name, str) and type_name in types else _seen
    resolved: dict[str, Any] = {}
    for key, value in resolved_node.items():
        if isinstance(value, dict):
            resolved[key] = _fully_resolve_declarative_node(value, types, seen_now, _memo)
        elif isinstance(value, list):
            resolved[key] = [
                _fully_resolve_declarative_node(item, types, seen_now, _memo) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            resolved[key] = value
    return resolved


def walk_type_tree_path(
    root: Mapping[str, Any],
    path: str,
    types: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
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
    :param types: optional named-type registry of the model the tree belongs
        to - lets the walk follow named type references (``{"type": "X"}``)
        and declarative polymorphic ``oneof`` nodes of a raw model definition
        (see _resolve_declarative_type_node). Leave it None for built
        artifacts (mapping/json schema), which need no resolution.
    :return: the "properties" mapping of the node reached by following `path`
    :raises KeyError: if any segment along the way is missing or not an object/array/polymorphic node
    :raises TypeError: if `root` is not a mapping
    """
    properties = root
    if not path:
        return properties

    path_list = path.split(".")
    memo: dict[str, dict[str, Any]] = {}
    while path_list:
        part = path_list.pop(0)
        if part not in properties:
            raise KeyError(f"Property {part} not found in {sorted(properties.keys())}")
        node = properties[part]
        if not isinstance(node, dict):
            raise TypeError(f"Properties at {part} must be a mapping, is {node}")
        node = _resolve_declarative_type_node(node, types, _memo=memo)
        if node.get("type") == "array":
            node = node.get("items")
            if not isinstance(node, dict):
                raise TypeError(f"Item members at {part} must be a mapping, is {node}")
            node = _resolve_declarative_type_node(node, types, _memo=memo)
        next_properties = node.get("properties")
        if not isinstance(next_properties, dict) and "oneOf" in node:
            # a JSON-Schema polymorphic node - union its inline branches
            next_properties = _merged_one_of_properties(node)
        if not isinstance(next_properties, dict):
            raise TypeError(
                f"Cannot descend into {part} - its node has no properties "
                f"(type {node.get('type', '<inline properties>')})"
            )
        properties = next_properties
    return cast("dict[str, Any]", properties)


type PathWalker = Callable[..., Mapping[str, Any]]
"""Signature shared by `walk_type_tree_path(root, path, types=...)` and `walk_ui_model_path(root, path)`.

Both take (root, path) plus walker-specific keyword arguments; a Protocol
spelling of this (``__call__(root, path, /, **kwargs)``) rejects implementations
that do not themselves accept arbitrary kwargs, so it stays a plain alias
(see the P2-F6 discussion in review.md).
"""


def _walk_path_leaf(
    walk: PathWalker,
    root: Mapping[str, Any],
    path: str,
    **walk_kwargs: Any,
) -> dict[str, Any]:
    """Resolve all but the last segment of `path` via `walk`, then return that last node.

    Shared by `walk_type_tree_path_leaf` and `walk_ui_model_path_leaf` - both
    do the same thing (descend to the leaf's parent, then index the leaf off
    it), differing only in which "walk the parent" function they use.

    :raises ValueError: if `path` is not specified
    :raises KeyError: if any segment is missing
    :raises TypeError: on unexpected types in the tree
    """
    if not path:
        raise ValueError("Path not specified")

    parts = path.split(".")
    parent_path = ".".join(parts[:-1])
    leaf = parts[-1]
    parent = walk(root, parent_path, **walk_kwargs)
    return cast("dict[str, Any]", parent[leaf])


def walk_type_tree_path_leaf(
    root: Mapping[str, Any],
    path: str,
    types: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Descend a dotted path and return the leaf node (not its properties).

    Like `walk_type_tree_path`, but returns the actual node at the end of the
    path instead of its "properties" mapping. This is useful when you want to
    retrieve a field definition (which may be a leaf with no "properties" key)
    rather than the properties of an object node.

    Uses `walk_type_tree_path` for all but the last segment to handle arrays
    correctly, then accesses the final segment directly. The leaf itself is
    fully resolved against `types` (see _fully_resolve_declarative_node): a
    key that *is* a named type (e.g. `molecular_weight: {"type": "Unit"}`)
    - and any named references inside its subtree - comes back inlined, so a
    cross-model relation does not copy a reference into a model that may not
    declare the named type. A genuinely self-referencing type can not be
    inlined and raises TypeError, as it does when walked.

    :param root: the "properties"-style mapping (field name -> declarative node)
        to start walking from.
    :param path: a dot-separated field path, e.g. "metadata.authors.name". Must
        be non-empty; an empty path raises `ValueError`.
    :param types: optional named-type registry - see walk_type_tree_path.
    :return: the node at the end of `path`
    :raises ValueError: if `path` is not specified
    :raises KeyError: if any segment is missing
    :raises TypeError: on unexpected types in the tree
    """
    leaf = _walk_path_leaf(walk_type_tree_path, root, path, types=types)
    return _fully_resolve_declarative_node(leaf, types, _memo={})


def walk_ui_model_path(root: Mapping[str, Any], path: str) -> dict[str, Any]:
    """Descend a dotted path through a UI model's "children"/"child"-shaped tree.

    Mirrors `walk_type_tree_path`, but for oarepo_model's UI model convention:
    a node's children live under "children", and an array node's single item
    node lives under "child" (the counterpart of "items" in `walk_type_tree_path`),
    transparently unwrapped before continuing the walk.

    :param root: the "children"-style mapping (field name -> UI model node) to
        start walking from.
    :param path: a dot-separated field path, e.g. "metadata.authors". An empty
        path returns `root` itself, unchanged.
    :return: the "children" mapping of the node reached by following `path`
    :raises KeyError: if any segment along the way is missing
    :raises TypeError: if `root` is not a mapping, or any segment along the way
        is not an object/array node
    """
    children: Any = root
    if not path:
        return cast("dict[str, Any]", children)
    for part in path.split("."):
        if part not in children:
            raise KeyError(f"Property {part} not found in {sorted(children.keys())}")
        node = children[part]
        if not isinstance(node, dict):
            raise TypeError(f"UI model node at {part} must be a mapping, is {node}")
        if "child" in node:
            node = node["child"]
            if not isinstance(node, dict):
                raise TypeError(f"UI model child at {part} must be a mapping, is {node}")
        next_children = node.get("children")
        if not isinstance(next_children, dict):
            raise TypeError(f"Children at {part} must be a mapping, is {next_children}")
        children = next_children
    return cast("dict[str, Any]", children)


def walk_ui_model_path_leaf(root: Mapping[str, Any], path: str) -> dict[str, Any]:
    """Descend a dotted path and return the leaf node (not its children).

    Like `walk_ui_model_path`, but returns the actual node at the end of the
    path instead of its "children" mapping.

    :param root: the "children"-style mapping (field name -> UI model node) to
        start walking from.
    :param path: a dot-separated field path, e.g. "metadata.authors.name". Must
        be non-empty; an empty path raises `ValueError`.
    :return: the node at the end of `path`
    :raises ValueError: if `path` is not specified
    :raises KeyError: if any segment is missing
    :raises TypeError: on unexpected types in the tree
    """
    return _walk_path_leaf(walk_ui_model_path, root, path)


class ArrayPathItem(Enum):
    """Enum backing the `ARRAY_PATH_ITEM` marker - see there for why this indirection exists."""

    ARRAY_PATH_ITEM = auto()


ARRAY_PATH_ITEM = ArrayPathItem.ARRAY_PATH_ITEM
"""Marker for array items in the path.

Used to indicate that a part of the path is an array item, differentiating
between simple relations and list relations.
"""

type ArrayPathMember = str | Literal[ArrayPathItem.ARRAY_PATH_ITEM]
"""A declarative field path segment: a field name, or the `ARRAY_PATH_ITEM` marker."""
