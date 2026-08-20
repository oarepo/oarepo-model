#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import json
from unittest.mock import MagicMock

from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations import AddJSONFile, CopyFile, PatchJSONFile
from oarepo_model.utils import resolve_file_content


def _builder_with_source():
    model = MagicMock()
    builder = InvenioModelBuilder(model, MagicMock())
    builder.add_module("mappings")
    AddJSONFile(
        "record-mapping",
        "mappings",
        "os-v2/record-metadata.json",
        {"mappings": {"properties": {"title": {"type": "keyword"}}}},
    ).apply(builder, model)
    CopyFile(
        source_symbolic_name="record-mapping",
        target_symbolic_name="draft-mapping",
        target_module_name="mappings",
        target_file_path="os-v2/draft-metadata.json",
    ).apply(builder, model)
    return builder, model


def _properties(builder, symbolic_name):
    content = resolve_file_content(builder.get_file(symbolic_name).content)
    return json.loads(content)["mappings"]["properties"]


def test_patching_copy_does_not_leak_into_source():
    builder, model = _builder_with_source()

    PatchJSONFile("draft-mapping", {"mappings": {"properties": {"expires_at": {"type": "date"}}}}).apply(builder, model)

    assert "expires_at" in _properties(builder, "draft-mapping")
    assert "expires_at" not in _properties(builder, "record-mapping")


def test_patching_source_does_not_leak_into_copy():
    builder, model = _builder_with_source()

    PatchJSONFile("record-mapping", {"mappings": {"properties": {"pid": {"type": "keyword"}}}}).apply(builder, model)

    assert "pid" in _properties(builder, "record-mapping")
    assert "pid" not in _properties(builder, "draft-mapping")
