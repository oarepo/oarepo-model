# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""PatchJSONFile detaches a patched file from the payload it was given.

deepmerge assigns values by reference, so a payload that is merged in without being
copied makes the generated file share its nested dicts/lists with the caller's dict -
and, when one dict is patched into several files (as DraftMappingPreset does with
`parent_mapping`), make those files share them with each other.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, cast
from unittest.mock import MagicMock

from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations import AddJSONFile, AddModule, PatchIndexMapping, PatchJSONFile
from oarepo_model.model import JSONContent
from oarepo_model.utils import resolve_file_content


def _builder() -> tuple[InvenioModelBuilder, MagicMock]:
    model = MagicMock()
    builder = InvenioModelBuilder(model, MagicMock())
    AddModule("mappings").apply(builder, model)
    return builder, model


def _add_empty_mapping(builder: InvenioModelBuilder, model: MagicMock, name: str, path: str) -> None:
    AddJSONFile(name, "mappings", path, {"mappings": {"properties": {}}}, exists_ok=True).apply(builder, model)


def _payload(builder: InvenioModelBuilder, name: str) -> dict[str, Any]:
    content = builder.get_file(name).content
    assert isinstance(content, JSONContent)
    return cast("dict[str, Any]", content.payload)


def test_one_payload_patched_into_two_files_does_not_alias_them():
    """One payload dict patched into two files must not make the files share subtrees."""
    builder, model = _builder()
    _add_empty_mapping(builder, model, "record-mapping", "record.json")
    _add_empty_mapping(builder, model, "draft-mapping", "draft.json")

    parent_mapping = {"mappings": {"properties": {"versions": {"properties": {"index": {"type": "integer"}}}}}}
    PatchJSONFile("draft-mapping", parent_mapping).apply(builder, model)
    PatchJSONFile("record-mapping", parent_mapping).apply(builder, model)

    record = _payload(builder, "record-mapping")
    draft = _payload(builder, "draft-mapping")
    assert record["mappings"]["properties"]["versions"] is not draft["mappings"]["properties"]["versions"]
    assert record["mappings"]["properties"]["versions"] is not parent_mapping["mappings"]["properties"]["versions"]

    # patching one file must leave the other one (and the caller's dict) alone
    PatchIndexMapping({"properties": {"versions": {"properties": {"index": None}}}}).apply(builder, model)

    assert json.loads(resolve_file_content(builder.get_file("record-mapping").content)) == {
        "mappings": {"properties": {"versions": {"properties": {}}}}
    }
    assert _payload(builder, "draft-mapping") == {
        "mappings": {"properties": {"versions": {"properties": {"index": {"type": "integer"}}}}},
    }
    assert parent_mapping == {
        "mappings": {"properties": {"versions": {"properties": {"index": {"type": "integer"}}}}},
    }


def test_payload_is_not_mutated_by_patching():
    """Applying a customization must not change the caller's payload, not even on a second apply."""
    builder, model = _builder()
    _add_empty_mapping(builder, model, "record-mapping", "record.json")

    payload: dict[str, Any] = {"mappings": {"properties": {"synonyms": {"type": "text", "synonyms": ["a", "b"]}}}}
    PatchJSONFile("record-mapping", payload).apply(builder, model)
    PatchJSONFile("record-mapping", payload).apply(builder, model)

    assert payload == {"mappings": {"properties": {"synonyms": {"type": "text", "synonyms": ["a", "b"]}}}}


def test_patch_does_not_realize_payloads_that_are_not_safe_to_touch_yet():
    """The existing content is patched in place, never deep-copied or normalized.

    A file's payload can hold lazily-resolved mappings that `JSONContent` only realizes
    when the file is dumped; copying or normalizing it here would resolve them during
    the build.
    """

    class NotYetResolvable(Mapping):
        def __len__(self) -> int:
            raise AssertionError("the payload must not be realized while the file is patched")

        def __iter__(self):
            raise AssertionError("the payload must not be realized while the file is patched")

        def __getitem__(self, key: str) -> Any:
            raise AssertionError("the payload must not be realized while the file is patched")

    lazy = NotYetResolvable()
    builder, model = _builder()
    builder.add_file(
        "record-mapping",
        "mappings",
        "record.json",
        JSONContent({"mappings": {"properties": {"relation": lazy}}}),
    )

    PatchJSONFile("record-mapping", {"mappings": {"properties": {"title": {"type": "keyword"}}}}).apply(builder, model)

    payload = _payload(builder, "record-mapping")
    assert payload["mappings"]["properties"]["relation"] is lazy
    assert payload["mappings"]["properties"]["title"] == {"type": "keyword"}


def test_patch_index_mapping_keeps_its_snippet_intact():
    """A `PatchIndexMapping` snippet survives the `recursively_remove_none` it is merged with."""
    builder, model = _builder()
    _add_empty_mapping(builder, model, "record-mapping", "record.json")

    snippet = {"properties": {"a": {"type": "text", "index": None, "fields": {"keyword": {"type": "keyword"}}}}}
    customization = PatchIndexMapping(snippet)
    customization.apply(builder, model)

    expected = {
        "mappings": {"properties": {"a": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}}},
    }
    assert json.loads(resolve_file_content(builder.get_file("record-mapping").content)) == expected

    # the same customization applied again (e.g. on another model) still patches
    # everything it was constructed with.
    assert snippet == {
        "properties": {"a": {"type": "text", "index": None, "fields": {"keyword": {"type": "keyword"}}}},
    }
    customization.apply(builder, model)
    assert json.loads(resolve_file_content(builder.get_file("record-mapping").content)) == expected
