#
# Copyright (c) 2026 University of West Bohemia
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Unit tests for the lazy-resolution primitives in oarepo_model.lazy.

The helper classes below are plain concrete subclasses of the abstract
classes under test (not mocks) - the classes are abstract precisely so
that behavior like laziness/caching, the Mapping protocol dispatch, and
the marshmallow schema-building logic can be exercised without needing a
fully built and registered model.
"""

from __future__ import annotations

from typing import Any

import marshmallow
import pytest

from oarepo_model.lazy import LazyJSONNamespaceFilePart, LazyMarshmallowSchema, LazyPythonMapping


class CountingLazyMapping(LazyPythonMapping):
    """A LazyPythonMapping that counts how many times it resolves its data."""

    def __init__(self, source: dict) -> None:
        """Initialize with the source data to resolve to."""
        super().__init__()
        self._source = source
        self.load_calls = 0

    def _load_data(self) -> dict:
        self.load_calls += 1
        return dict(self._source)


class DictJSONNamespaceFilePart(LazyJSONNamespaceFilePart):
    """A LazyJSONNamespaceFilePart resolved against an in-memory dict instead of a real runtime module."""

    def __init__(self, source: dict, **kwargs: Any) -> None:
        """Initialize with the source data to resolve paths against."""
        super().__init__(model="unused", filename="unused", **kwargs)
        self._source = source

    def _load_original_json(self) -> dict:
        return self._source

    def _get_path(self, data: Any, path: str) -> Any:
        node = data
        for part in path.split("."):
            node = node[part]
        return node

    def _set_path(self, data: Any, path: str, value: Any) -> None:
        parts = path.split(".")
        node = data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value


class DictJSONNamespaceFilePartWithExtraFields(DictJSONNamespaceFilePart):
    """A DictJSONNamespaceFilePart that always contributes an 'id' extra field."""

    extra_fields = {"id": 42}  # noqa: RUF012


class DefaultLazyMarshmallowSchema(LazyMarshmallowSchema):
    """A LazyMarshmallowSchema that does not override _get_target_schema/_missing_field."""

    model = "unused"


class LazyMarshmallowSchemaAgainstFixedTarget(LazyMarshmallowSchema):
    """A LazyMarshmallowSchema resolved against a fixed, in-memory target schema."""

    model = "unused"

    @classmethod
    def _get_target_schema(cls) -> marshmallow.Schema:
        class TargetSchema(marshmallow.Schema):
            title = marshmallow.fields.String()

        return TargetSchema()


class LazyMarshmallowSchemaAgainstNestedTarget(LazyMarshmallowSchema):
    """A LazyMarshmallowSchema resolved against a target schema with a nested field."""

    model = "unused"

    @classmethod
    def _get_target_schema(cls) -> marshmallow.Schema:
        class InnerSchema(marshmallow.Schema):
            leaf = marshmallow.fields.String()

        class TargetSchema(marshmallow.Schema):
            nested = marshmallow.fields.Nested(InnerSchema)

        return TargetSchema()


# ---------------------------------------------------------------------------
# LazyPythonMapping
# ---------------------------------------------------------------------------


@pytest.fixture
def counting_mapping():
    return CountingLazyMapping({"a": 1, "b": 2})


def test_lazy_python_mapping_not_loaded_before_first_access(counting_mapping):
    assert counting_mapping.load_calls == 0


def test_lazy_python_mapping_getitem_triggers_and_caches_load(counting_mapping):
    assert counting_mapping["a"] == 1
    assert counting_mapping.load_calls == 1
    assert counting_mapping["b"] == 2
    # second access must not reload the data
    assert counting_mapping.load_calls == 1


def test_lazy_python_mapping_iter_triggers_load_and_yields_keys(counting_mapping):
    assert sorted(counting_mapping) == ["a", "b"]
    assert counting_mapping.load_calls == 1


def test_lazy_python_mapping_len_triggers_load(counting_mapping):
    assert len(counting_mapping) == 2
    assert counting_mapping.load_calls == 1


def test_lazy_python_mapping_behaves_as_mapping(counting_mapping):
    assert dict(counting_mapping) == {"a": 1, "b": 2}
    assert "a" in counting_mapping
    assert "z" not in counting_mapping


# ---------------------------------------------------------------------------
# LazyJSONNamespaceFilePart
# ---------------------------------------------------------------------------


@pytest.fixture
def json_part():
    return DictJSONNamespaceFilePart({"a": 1, "b": 2}, keys=["a", "b"], initial_content={})


def test_json_namespace_file_part_len_and_getitem_resolve_from_source(json_part):
    assert len(json_part) == 2
    assert json_part["a"] == 1
    assert json_part["b"] == 2


@pytest.fixture
def json_part_with_initial_content():
    initial = {"x": 1}
    part = DictJSONNamespaceFilePart({"a": 1}, keys=["a"], initial_content=initial)
    return part, initial


def test_json_namespace_file_part_initial_content_is_preserved_and_not_mutated(json_part_with_initial_content):
    part, initial = json_part_with_initial_content
    assert dict(part) == {"x": 1, "a": 1}
    # the source initial_content mapping itself must not be mutated in place
    assert initial == {"x": 1}


@pytest.fixture
def json_part_with_extra_field():
    return DictJSONNamespaceFilePartWithExtraFields({}, keys=[], initial_content={})


def test_json_namespace_file_part_extra_fields_added_when_not_already_present(json_part_with_extra_field):
    assert json_part_with_extra_field["id"] == 42


@pytest.fixture
def json_part_with_extra_field_already_resolved():
    return DictJSONNamespaceFilePartWithExtraFields({"id": 1}, keys=["id"], initial_content={})


def test_json_namespace_file_part_extra_fields_do_not_override_resolved_keys(
    json_part_with_extra_field_already_resolved,
):
    assert json_part_with_extra_field_already_resolved["id"] == 1


# ---------------------------------------------------------------------------
# LazyMarshmallowSchema
# ---------------------------------------------------------------------------


@pytest.fixture
def default_marshmallow_schema():
    schema = DefaultLazyMarshmallowSchema()
    schema.keys = ["id"]
    return schema


def test_lazy_marshmallow_schema_default_get_target_schema_raises(default_marshmallow_schema):
    with pytest.raises(NotImplementedError):
        _ = default_marshmallow_schema.proxied_schema


@pytest.fixture
def fixed_target_marshmallow_schema():
    return LazyMarshmallowSchemaAgainstFixedTarget()


def test_lazy_marshmallow_schema_default_missing_field_raises_key_error(fixed_target_marshmallow_schema):
    fixed_target_marshmallow_schema.keys = ["does_not_exist"]
    with pytest.raises(KeyError):
        _ = fixed_target_marshmallow_schema.proxied_schema


def test_lazy_marshmallow_schema_missing_intermediate_segment_falls_back_to_missing_field(
    fixed_target_marshmallow_schema,
):
    # "nope" (the first segment) does not exist at all on the target schema,
    # so the key can't be resolved and falls back to the default _missing_field.
    fixed_target_marshmallow_schema.keys = ["nope.sub"]
    with pytest.raises(KeyError):
        _ = fixed_target_marshmallow_schema.proxied_schema


def test_lazy_marshmallow_schema_intermediate_non_nested_field_raises_type_error(fixed_target_marshmallow_schema):
    # "title" is a plain String field, not Nested - descending into it
    # (as "title.sub") is invalid.
    fixed_target_marshmallow_schema.keys = ["title.sub"]
    with pytest.raises(TypeError):
        _ = fixed_target_marshmallow_schema.proxied_schema


def test_lazy_marshmallow_schema_resolves_leaf_field_and_loads_dumps(fixed_target_marshmallow_schema):
    fixed_target_marshmallow_schema.keys = ["title"]
    loaded = fixed_target_marshmallow_schema.load({"title": "hello"})
    assert loaded == {"title": "hello"}
    assert fixed_target_marshmallow_schema.dump(loaded) == {"title": "hello"}


def test_lazy_marshmallow_schema_uses_initial_schema_before_target(fixed_target_marshmallow_schema):
    class InitialSchema(marshmallow.Schema):
        extra = marshmallow.fields.Integer()

    fixed_target_marshmallow_schema.initial_schema = InitialSchema()
    # "extra" only exists on initial_schema, not on the fixed target schema -
    # resolving it successfully proves initial_schema is consulted first.
    fixed_target_marshmallow_schema.keys = ["extra"]
    loaded = fixed_target_marshmallow_schema.load({"extra": 5})
    assert loaded == {"extra": 5}


@pytest.fixture
def nested_target_marshmallow_schema():
    schema = LazyMarshmallowSchemaAgainstNestedTarget()
    schema.keys = ["nested.leaf"]
    return schema


def test_lazy_marshmallow_schema_resolves_nested_field_and_loads_dumps(nested_target_marshmallow_schema):
    loaded = nested_target_marshmallow_schema.load({"nested": {"leaf": "hello"}})
    assert loaded == {"nested": {"leaf": "hello"}}
    assert nested_target_marshmallow_schema.dump(loaded) == {"nested": {"leaf": "hello"}}
