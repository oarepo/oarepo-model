#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""CopyFile copies a file's content by reference, which aliases JSON payloads.

`PatchJSONFile` patches a `JSONContent`'s payload dict in place (`always_merger.merge`
returns its mutated left operand) and `CopyFile` hands the very same `JSONContent`
object to the target file, so once a JSON file has been patched, every copy taken of
it shares one payload dict - patching either file afterwards rewrites both.

The shipped drafts presets patch "record-mapping" and "draft-mapping" symmetrically
(see DraftMappingPreset, which yields the same `parent_mapping` to both), so this is
invisible in a default model - but their payloads really are one dict, and any patch
that isn't symmetric lands in both files.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations import AddJSONFile, AddModule, CopyFile, PatchJSONFile
from oarepo_model.utils import resolve_file_content

ALIASED_PAYLOAD = "CopyFile shares the source's JSONContent payload dict with the copy"

ORIGINAL_MAPPING = {"mappings": {"properties": {"title": {"type": "keyword"}}}}
RECORD_ONLY = {"mappings": {"properties": {"only_record": {"type": "keyword"}}}}


@pytest.mark.xfail(reason=ALIASED_PAYLOAD, strict=True, raises=AssertionError)
def test_patching_a_file_after_it_was_copied_leaves_the_copy_alone():
    """A patch applied to the source after CopyFile must not reach the target."""
    model = MagicMock()
    builder = InvenioModelBuilder(model, MagicMock())
    AddModule("mappings").apply(builder, model)
    AddJSONFile("record-mapping", "mappings", "record.json", ORIGINAL_MAPPING).apply(builder, model)

    # the file's content is only a JSONContent (rather than a json string) once it
    # has been patched at least once - that is what the copy then aliases.
    PatchJSONFile("record-mapping", {"mappings": {"properties": {"shared": {"type": "keyword"}}}}).apply(builder, model)
    CopyFile("record-mapping", "draft-mapping", "mappings", "draft.json").apply(builder, model)
    PatchJSONFile("record-mapping", RECORD_ONLY).apply(builder, model)

    copied = json.loads(resolve_file_content(builder.get_file("draft-mapping").content))
    assert "shared" in copied["mappings"]["properties"], "the copy lost what the source had at copy time"
    assert "only_record" not in copied["mappings"]["properties"]


@pytest.mark.xfail(reason=ALIASED_PAYLOAD, strict=True, raises=AssertionError)
def test_draft_mapping_patch_does_not_leak_into_the_record_mapping():
    """The same aliasing on a real drafts model, via a user customization on "draft-mapping"."""
    from oarepo_model.api import model
    from oarepo_model.presets.drafts import drafts_preset
    from oarepo_model.presets.records_resources import records_resources_preset

    name = "copy_file_leak_test"
    m = model(
        name=name,
        version="1.0.0",
        presets=[records_resources_preset, drafts_preset],
        types=[{"Metadata": {"properties": {"title": {"type": "keyword"}}}}],
        metadata_type="Metadata",
        # a user customization named "draft-mapping" is applied after
        # DraftMappingPreset has already copied "record-mapping" (see the
        # depends_on-driven ordering in api._internal_model); a PatchIndexMapping
        # on "record-mapping" happens to be applied *before* that copy, so it is
        # the draft side that shows the leak.
        customizations=[
            PatchJSONFile("draft-mapping", {"mappings": {"properties": {"only_draft": {"type": "keyword"}}}}),
        ],
    )

    files = m.__files__
    record = json.loads(resolve_file_content(files[f"mappings/os-v2/{name}/metadata-v1.0.0.json"]))
    draft = json.loads(resolve_file_content(files[f"mappings/os-v2/{name}/draft-metadata-v1.0.0.json"]))

    assert "only_draft" in draft["mappings"]["properties"]
    assert "only_draft" not in record["mappings"]["properties"]
