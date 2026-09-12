# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations


def test_parent_model_field(
    identity_simple,
    model_types,
    draft_model,
    draft_model_with_files,
    location,
    search_clear,
):
    draft_model.proxies.current_service.create(identity_simple, data={})
    draft_model_with_files.proxies.current_service.create(identity_simple, data={"files": {"enabled": True}})

    assert draft_model.ParentRecordMetadata.query.one().model == "draft_test"
    assert draft_model_with_files.ParentRecordMetadata.query.one().model == "draft_with_files"
