# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Ordering of user customizations passed to model(customizations=[...]).

A customization is applied before the first preset that declares the partial it
modifies in depends_on (and before that preset's dependencies are built); the
rest are applied after all presets, in the order they were passed.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.services import ExternalLink
from invenio_records_resources.services.records.params.base import ParamInterpreter

from oarepo_model.api import model
from oarepo_model.customizations import (
    AddList,
    AddParamInterpreterCls,
    AddToDictionary,
    AddToList,
    PatchJSONFile,
    SetDefaultSearchFields,
)
from oarepo_model.customizations.high_level.add_link import AddLink
from oarepo_model.presets import Preset
from oarepo_model.presets.drafts import drafts_records_preset
from oarepo_model.presets.records_resources import records_preset
from oarepo_model.utils import resolve_file_content

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel

#: what each depender preset saw in its built dependencies, keyed by preset name
SEEN: dict[str, list[Any]] = {}

_types = {"Metadata": {"properties": {"title": {"type": "fulltext+keyword"}}}}


class ProvidesListPreset(Preset):
    """Preset that creates the list partial used by the tests."""

    provides = ("order_test",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Any]:
        yield AddList("order_test", exists_ok=True)


class ProvidesOtherListPreset(Preset):
    """Preset that creates the other_list partial."""

    provides = ("other_list",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Any]:
        yield AddList("other_list", exists_ok=True)


class UsesListPreset(Preset):
    """Preset that records what the 'order_test' partial contained when it ran."""

    depends_on = ("order_test",)
    seen_key = "uses_list"

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Any]:
        SEEN.setdefault(self.seen_key, []).append(list(dependencies["order_test"]))
        yield from ()


class SecondUsesListPreset(UsesListPreset):
    """Another depender, to check the customization is applied only once."""

    seen_key = "second_uses_list"


class UsesLinksPreset(Preset):
    """Preset that reads the built record_links_item dictionary."""

    depends_on = ("record_links_item",)
    seen_key = "uses_links"

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Any]:
        SEEN.setdefault(self.seen_key, []).append(dict(dependencies["record_links_item"]))
        yield from ()


def _mapping(m: Any, name: str, file: str) -> dict[str, Any]:
    return json.loads(resolve_file_content(m.__files__[f"mappings/os-v2/{name}/{file}"]))


def test_customization_applied_before_depending_preset():
    SEEN.clear()
    m = model(
        name="uco_before_depender",
        version="1.0.0",
        presets=[ProvidesListPreset, UsesListPreset],
        customizations=[AddToList("order_test", "user-item")],
    )

    # visible to the depender's built dependencies ...
    assert SEEN["uses_list"] == [["user-item"]]
    # ... and exactly once in the final model
    assert m.order_test == ["user-item"]


def test_customization_applied_once_for_all_depending_presets():
    SEEN.clear()
    model(
        name="uco_two_dependers",
        version="1.0.0",
        presets=[ProvidesListPreset, UsesListPreset, SecondUsesListPreset],
        customizations=[AddToList("order_test", "user-item")],
    )

    # both dependers see it (the second one through the cached build)
    assert SEEN["uses_list"] == [["user-item"]]
    assert SEEN["second_uses_list"] == [["user-item"]]


def test_matching_customization_runs_before_end_applied_ones():
    SEEN.clear()
    m = model(
        name="uco_pull_forward",
        version="1.0.0",
        presets=[ProvidesListPreset, ProvidesOtherListPreset, UsesListPreset],
        customizations=[
            # listed first, but has no matching depender, so it is applied last
            AddToList("other_list", "late-item"),
            # listed last, but pulled forward before the depender preset
            AddToList("order_test", "user-item"),
        ],
    )

    assert SEEN["uses_list"] == [["user-item"]]
    assert m.other_list == ["late-item"]


def test_end_applied_customizations_preserve_list_order():
    m = model(
        name="uco_end_order",
        version="1.0.0",
        presets=[ProvidesListPreset],
        customizations=[
            AddToList("order_test", "first-item"),
            AddToList("order_test", "second-item"),
        ],
    )

    assert m.order_test == ["first-item", "second-item"]


def test_add_to_dictionary_on_depended_dictionary():
    def computed(_):
        return 42

    m = model(
        name="uco_synthetic_metadata",
        version="1.0.0",
        presets=[records_preset],
        types=[_types],
        metadata_type="Metadata",
        customizations=[AddToDictionary("synthetic_metadata", key="computed", value=computed)],
    )

    # RecordPreset depends on synthetic_metadata and builds a snapshot of it,
    # so this only works if the customization ran before that preset
    assert m.synthetic_metadata["computed"] is computed


def test_add_param_interpreter_cls_in_built_model():
    class MyParamInterpreter(ParamInterpreter):
        """Test param interpreter, never instantiated."""

    m = model(
        name="uco_param_interpreter",
        version="1.0.0",
        presets=[records_preset],
        types=[_types],
        metadata_type="Metadata",
        customizations=[AddParamInterpreterCls(MyParamInterpreter)],
    )

    assert MyParamInterpreter in m.extra_param_interpreter_classes


def test_set_default_search_fields_reaches_draft_mapping():
    name = "uco_default_search_fields"
    m = model(
        name=name,
        version="1.0.0",
        presets=[records_preset, drafts_records_preset],
        types=[_types],
        metadata_type="Metadata",
        customizations=[SetDefaultSearchFields("metadata.title")],
    )

    # DraftMappingPreset derives draft-mapping from record-mapping, so the
    # customization must run before it
    record = _mapping(m, name, "metadata-v1.0.0.json")
    draft = _mapping(m, name, "draft-metadata-v1.0.0.json")
    assert record["settings"]["index.query.default_field"] == ["metadata.title"]
    assert draft["settings"]["index.query.default_field"] == ["metadata.title"]


def test_patch_json_file_on_record_mapping_reaches_draft_mapping():
    name = "uco_patch_record_mapping"
    m = model(
        name=name,
        version="1.0.0",
        presets=[records_preset, drafts_records_preset],
        types=[_types],
        metadata_type="Metadata",
        customizations=[
            PatchJSONFile("record-mapping", {"mappings": {"properties": {"user_prop": {"type": "keyword"}}}}),
        ],
    )

    record = _mapping(m, name, "metadata-v1.0.0.json")
    draft = _mapping(m, name, "draft-metadata-v1.0.0.json")
    assert record["mappings"]["properties"]["user_prop"] == {"type": "keyword"}
    assert draft["mappings"]["properties"]["user_prop"] == {"type": "keyword"}


def test_modifies_declared_customization_applies_before_depender():
    """AddLink's name is not the partial it modifies, its modifies declaration is."""
    SEEN.clear()
    tested_link = ExternalLink("/not/a/link")
    m = model(
        name="uco_declared_modifies",
        version="1.0.0",
        presets=[records_preset, UsesLinksPreset],
        types=[_types],
        metadata_type="Metadata",
        customizations=[AddLink("test_link", tested_link)],
    )

    # UsesLinksPreset builds record_links_item from its depends_on, so the link
    # must have been added before that - not in the trailing loop, where the
    # already-built dictionary would reject the mutation
    assert SEEN["uses_links"][0]["test_link"] is tested_link
    assert m.record_links_item["test_link"] is tested_link
