# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

import sys
import types
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from oarepo_model.datatypes.relations import PIDRelation


@pytest.fixture
def datatype_registry():
    from oarepo_model.datatypes.registry import DataTypeRegistry

    registry = DataTypeRegistry()
    registry.load_entry_points()
    return registry


@pytest.fixture
def pid_relation(datatype_registry) -> PIDRelation:
    return datatype_registry.get_type({"type": "pid-relation"})


@pytest.fixture
def register_fake_runtime_model():
    """Register (and clean up) a real 'runtime_models_<name>' module for a test.

    Not a mock - PIDRelation._get_target_properties just does
    importlib.import_module("runtime_models_<name>") (see
    oarepo_model.utils.import_runtime_model), so a genuine types.ModuleType
    inserted into sys.modules is enough to exercise the real import
    machinery, without needing to actually build a full oarepo model.
    """
    created = []

    def _register(model_name: str, **attrs: Any) -> None:
        module_name = f"runtime_models_{model_name}"
        module = types.ModuleType(module_name)
        for key, value in attrs.items():
            setattr(module, key, value)
        sys.modules[module_name] = module
        created.append(module_name)

    yield _register

    for module_name in created:
        del sys.modules[module_name]


# ---------------------------------------------------------------------------
# PIDRelation._get_properties / _lookup_target_element / _get_target_properties
# ---------------------------------------------------------------------------


def test_get_properties_reraises_when_model_unresolvable_and_not_ignoring(pid_relation):
    element = {"model": "does_not_exist_at_all", "keys": ["id"]}
    with pytest.raises(ModuleNotFoundError):
        pid_relation._get_properties(element, ignore_missing=False)


def test_get_properties_raises_key_error_with_model_name_in_message(pid_relation, register_fake_runtime_model):
    register_fake_runtime_model("fake_empty_model")  # no oarepo_model_arguments -> target_properties == {}
    element = {"model": "fake_empty_model", "keys": ["nonexistent_key"]}
    with pytest.raises(KeyError, match=r"nonexistent_key.*fake_empty_model"):
        pid_relation._get_properties(element, ignore_missing=False)


def test_get_properties_raises_key_error_without_model_name(pid_relation):
    # no "model" key at all - target_properties is {} without even trying to import anything.
    element = {"keys": ["nonexistent_key"]}
    with pytest.raises(KeyError, match="Model name is not available"):
        pid_relation._get_properties(element, ignore_missing=False)


def test_get_properties_raises_type_error_for_invalid_key_type(pid_relation):
    element = {"keys": [123]}
    with pytest.raises(TypeError, match="Invalid key type"):
        pid_relation._get_properties(element)


def test_lookup_target_element_returns_none_for_malformed_properties_value(pid_relation):
    # "parent.properties" is a string, not a dict - the path can't be descended into.
    malformed_properties = {"parent": {"properties": "not-a-dict"}}
    assert pid_relation._lookup_target_element(malformed_properties, "parent.child") is None


def test_get_target_properties_returns_empty_when_no_model_metadata(pid_relation, register_fake_runtime_model):
    register_fake_runtime_model("fake_no_metadata")
    properties = pid_relation._get_target_properties({"model": "fake_no_metadata"})
    assert properties == {}


def test_get_target_properties_includes_record_and_metadata_type_properties(
    pid_relation,
    register_fake_runtime_model,
):
    from oarepo_runtime.api import ModelMetadata

    model_metadata = ModelMetadata(
        types={
            "Record": {"properties": {"pid": {"type": "keyword"}}},
            "Metadata": {"properties": {"title": {"type": "keyword"}}},
        },
        record_type="Record",
        metadata_type="Metadata",
    )
    register_fake_runtime_model(
        "fake_with_record_type",
        oarepo_model_arguments={"model_metadata": model_metadata},
    )
    properties = pid_relation._get_target_properties({"model": "fake_with_record_type"})
    assert properties["pid"] == {"type": "keyword"}
    assert properties["metadata"] == {"properties": {"title": {"type": "keyword"}}}


# ---------------------------------------------------------------------------
# PIDRelation._relation_pid_field / _relation_key_names
# ---------------------------------------------------------------------------


def test_relation_pid_field_calls_resolved_pid_field(pid_relation):
    def _pid_field_getter(element: dict[str, Any]) -> list[str]:
        return element["keys"]

    element = {"pid_field": _pid_field_getter, "keys": ["id"]}
    assert pid_relation._relation_pid_field(element, []) == ["id"]


@pytest.mark.parametrize(
    ("element", "match"),
    [
        ({"pid_field": 42}, "could not be imported"),  # a non-string, non-callable, truthy value
        ({"record_cls": object()}, "does not have a 'pid' attribute"),
        ({}, "Either 'pid_field' or 'record_cls'"),
    ],
    ids=["pid_field_not_callable", "record_cls_has_no_pid", "neither_pid_field_nor_record_cls"],
)
def test_relation_pid_field_raises_value_error(pid_relation, element, match):
    with pytest.raises(ValueError, match=match):
        pid_relation._relation_pid_field(element, [])


def test_relation_key_names_raises_type_error_for_invalid_key_type(pid_relation):
    element = {"keys": [123]}
    with pytest.raises(TypeError, match="Invalid key type"):
        pid_relation._relation_key_names(element, [])


def test_relations(
    app,
    identity_simple,
    empty_model,
    relation_model,
    search,
    search_clear,
    location,
):
    TargetRecord = empty_model.Record
    target_service = empty_model.proxies.current_service

    # Create the target records

    rec1_id = target_service.create(
        identity_simple,
        {"files": {"enabled": False}, "metadata": {"title": "Record 1"}},
    ).id
    rec2_id = target_service.create(
        identity_simple,
        {"files": {"enabled": False}, "metadata": {"title": "Record 2"}},
    ).id
    rec3_id = target_service.create(
        identity_simple,
        {"files": {"enabled": False}, "metadata": {"title": "Record 3"}},
    ).id

    # Refresh to make changes live
    TargetRecord.index.refresh()

    relation_service = relation_model.proxies.current_service

    relation_rec = relation_service.create(
        identity_simple,
        {
            "files": {
                "enabled": False,
            },
            "metadata": {
                "direct": {
                    "id": rec1_id,
                },
                "array": [
                    {"id": rec1_id},
                    {"id": rec2_id},
                ],
                "object": {
                    "a": {"id": rec1_id},
                },
                "double_array": [
                    {"array": [{"id": rec1_id}, {"id": rec2_id}]},
                    {"array": [{"id": rec3_id}]},
                ],
                "triple_array": [
                    {
                        "array": [
                            {"array": [{"id": rec1_id}]},
                            {"array": [{"id": rec2_id}, {"id": rec3_id}]},
                        ]
                    }
                ],
            },
        },
    )

    md = relation_rec.data["metadata"]
    assert md["direct"]["id"] == rec1_id
    assert md["direct"]["metadata"]["title"] == "Record 1"

    assert len(md["array"]) == 2
    assert md["array"][0]["id"] == rec1_id
    assert md["array"][0]["metadata"]["title"] == "Record 1"
    assert md["array"][1]["id"] == rec2_id
    assert md["array"][1]["metadata"]["title"] == "Record 2"

    assert md["object"]["a"]["id"] == rec1_id
    assert md["object"]["a"]["metadata"]["title"] == "Record 1"

    assert len(md["double_array"]) == 2
    assert len(md["double_array"][0]["array"]) == 2
    assert md["double_array"][0]["array"][0]["id"] == rec1_id
    assert md["double_array"][0]["array"][0]["metadata"]["title"] == "Record 1"
    assert md["double_array"][0]["array"][1]["id"] == rec2_id
    assert md["double_array"][0]["array"][1]["metadata"]["title"] == "Record 2"
    assert len(md["double_array"][1]["array"]) == 1
    assert md["double_array"][1]["array"][0]["id"] == rec3_id
    assert md["double_array"][1]["array"][0]["metadata"]["title"] == "Record 3"

    assert len(md["triple_array"]) == 1
    assert len(md["triple_array"][0]["array"]) == 2
    assert len(md["triple_array"][0]["array"][0]["array"]) == 1
    assert md["triple_array"][0]["array"][0]["array"][0]["id"] == rec1_id
    assert md["triple_array"][0]["array"][0]["array"][0]["metadata"]["title"] == "Record 1"
    assert len(md["triple_array"][0]["array"][1]["array"]) == 2
    assert md["triple_array"][0]["array"][1]["array"][0]["id"] == rec2_id
    assert md["triple_array"][0]["array"][1]["array"][0]["metadata"]["title"] == "Record 2"
    assert md["triple_array"][0]["array"][1]["array"][1]["id"] == rec3_id
    assert md["triple_array"][0]["array"][1]["array"][1]["metadata"]["title"] == "Record 3"
