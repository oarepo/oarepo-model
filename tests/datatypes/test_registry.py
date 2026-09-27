# SPDX-FileCopyrightText: 2026 University of West Bohemia
# SPDX-License-Identifier: MIT

"""Tests for DataTypeRegistry and loader functions.

Covers:
- from_json: dict format and list format (with and without origin)
- from_json/from_yaml: scalar content raises TypeError
- from_yaml: dict format and list format (with and without origin)
- get_type: unknown type raises KeyError
- get_type: dict with neither type/properties/items raises ValueError
- add_types: invalid type value (not dict, not DataType subclass) raises TypeError
- add_types with DataType subclass
- registry.items() returns all registered types
- Duplicate type registration emits a warning (or silently overwrites)
"""

from __future__ import annotations

import json

import pytest
import yaml

from oarepo_model.datatypes.registry import from_json, from_yaml

# ===========================================================================
# from_json / from_yaml
# ===========================================================================


@pytest.mark.parametrize(
    ("loader", "dump", "suffix"),
    [(from_json, json.dumps, "json"), (from_yaml, yaml.dump, "yaml")],
    ids=["json", "yaml"],
)
class TestLoaders:
    """from_json and from_yaml must parse both dict and list formats."""

    def test_dict_format_returns_dict(self, tmp_path, loader, dump, suffix):
        """Return the mapping unchanged when the file uses the dict format."""
        path = tmp_path / f"types.{suffix}"
        path.write_text(dump({"MyType": {"type": "keyword"}}), encoding="utf-8")
        assert loader(str(path)) == {"MyType": {"type": "keyword"}}

    def test_list_format_returns_dict_keyed_by_popped_name(self, tmp_path, loader, dump, suffix):
        """Return one key per list element, keyed by its popped name field."""
        path = tmp_path / f"types.{suffix}"
        path.write_text(
            dump([{"name": "TypeA", "type": "keyword"}, {"name": "TypeB", "type": "fulltext"}]),
            encoding="utf-8",
        )
        assert loader(str(path)) == {"TypeA": {"type": "keyword"}, "TypeB": {"type": "fulltext"}}

    def test_origin_resolves_relative_path(self, tmp_path, loader, dump, suffix):
        """When origin is given, file_name is resolved relative to its parent dir."""
        origin_file = tmp_path / "subdir" / "origin.py"
        origin_file.parent.mkdir()
        origin_file.write_text("")
        (tmp_path / "subdir" / f"types.{suffix}").write_text(dump({"T": {"type": "int"}}), encoding="utf-8")

        assert loader(f"types.{suffix}", origin=str(origin_file)) == {"T": {"type": "int"}}

    def test_scalar_content_raises_type_error(self, tmp_path, loader, dump, suffix):
        """Raise TypeError when the file's top-level content is neither a list nor a dict."""
        path = tmp_path / f"types.{suffix}"
        path.write_text(dump(42), encoding="utf-8")
        with pytest.raises(TypeError, match="Expected dict or list"):
            loader(str(path))


# ===========================================================================
# get_type error paths
# ===========================================================================


class TestGetTypeErrorPaths:
    """get_type must raise clear errors for unknown or ambiguous inputs."""

    def test_unknown_string_type_raises_key_error(self, datatype_registry):
        """Raise KeyError naming the type when no datatype carries that name."""
        with pytest.raises(KeyError, match="not_a_real_type"):
            datatype_registry.get_type("not_a_real_type")

    def test_dict_without_type_or_properties_or_items_raises_value_error(self, datatype_registry):
        """Raise ValueError when a dict offers no type, properties or items key."""
        with pytest.raises(ValueError, match=r"."):
            datatype_registry.get_type({"something": "else"})

    def test_dict_with_type_key_resolves_correctly(self, datatype_registry):
        """Resolve a dict carrying a type key to the datatype that key names."""
        from oarepo_model.datatypes.strings import KeywordDataType

        dt = datatype_registry.get_type({"type": "keyword"})
        assert isinstance(dt, KeywordDataType)

    def test_dict_with_properties_key_resolves_to_object(self, datatype_registry):
        """Resolve a dict with a properties key to the object datatype."""
        from oarepo_model.datatypes.collections import ObjectDataType

        dt = datatype_registry.get_type({"properties": {"x": {"type": "int"}}})
        assert isinstance(dt, ObjectDataType)

    def test_dict_with_items_key_resolves_to_array(self, datatype_registry):
        """Resolve a dict with an items key to the array datatype."""
        from oarepo_model.datatypes.collections import ArrayDataType

        dt = datatype_registry.get_type({"items": {"type": "int"}})
        assert isinstance(dt, ArrayDataType)


# ===========================================================================
# add_types error paths
# ===========================================================================


class TestAddTypesErrorPaths:
    """add_types must raise TypeError for values that are neither dicts nor DataType subclasses."""

    @pytest.mark.parametrize("bad_value", [42, "not_a_class", int], ids=["int", "string", "non-datatype-class"])
    def test_add_types_with_invalid_value_raises_type_error(self, datatype_registry, bad_value):
        """Reject a value that is neither a dict nor a DataType subclass with TypeError."""
        with pytest.raises(TypeError, match="Expected a dict or a subclass of DataType"):
            datatype_registry.add_types({"BadType": bad_value})

    def test_add_types_with_dict_registers_wrapped_datatype(self, datatype_registry):
        """Register a dict definition as a WrappedDataType under the given name."""
        from oarepo_model.datatypes.wrapped import WrappedDataType

        datatype_registry.add_types({"CustomKw": {"type": "keyword"}})
        dt = datatype_registry.get_type("CustomKw")
        assert isinstance(dt, WrappedDataType)

    def test_add_types_with_datatype_subclass_registers_instance(self, datatype_registry):
        """Register a DataType subclass as an instance of that subclass."""
        from oarepo_model.datatypes.strings import KeywordDataType

        datatype_registry.add_types({"MyKeyword": KeywordDataType})
        dt = datatype_registry.get_type("MyKeyword")
        assert isinstance(dt, KeywordDataType)


class TestRegistryItems:
    """items() must expose all registered types as (name, DataType) pairs."""

    def test_items_contains_builtin_types(self, datatype_registry):
        """Expose the builtin keyword, fulltext, numeric and boolean types."""
        names = {name for name, _ in datatype_registry.items()}
        for expected in ("keyword", "fulltext", "fulltext+keyword", "int", "float", "boolean"):
            assert expected in names, f"Expected {expected!r} in registry"

    def test_items_reflects_add_types(self, datatype_registry):
        """Expose a name added through add_types among the registry items."""
        datatype_registry.add_types({"UniqueTestType999": {"type": "keyword"}})
        names = {name for name, _ in datatype_registry.items()}
        assert "UniqueTestType999" in names


# ===========================================================================
# Duplicate registration
# ===========================================================================


class TestDuplicateRegistration:
    """Registering a type name twice must overwrite the old registration."""

    def test_duplicate_type_overwrites_silently(self, datatype_registry):
        """Override the first registration so the last mapping added wins."""
        datatype_registry.add_types({"DupType": {"type": "keyword"}})
        datatype_registry.add_types({"DupType": {"type": "fulltext"}})
        # The second registration wins; the type should produce a text mapping.
        dt = datatype_registry.get_type("DupType")
        mapping = dt.create_mapping({"type": "DupType"})
        assert mapping["type"] == "text"
