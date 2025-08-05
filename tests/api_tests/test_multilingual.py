#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations


def test_multilingual(
    app,
    identity_simple,
    empty_model,
    multilingual_model,
    search,
    search_clear,
    location,
):
    record_with_vocabulary_service = multilingual_model.proxies.current_service

    vocabulary_rec = record_with_vocabulary_service.create(
        identity_simple,
        {
            "files": {
                "enabled": False,
            },
            "metadata": {
                "title": {"lang": "en", "value": "yaay"},
                "abstract": {"jazyk": "cs", "hodnotka": "jeeej"},
                "rights": [{"lang": "cs", "value": "jeeej"}, {"lang": "en", "value": "yeeey"}],
            },
        },
    )

    md = vocabulary_rec.data["metadata"]

    assert md == {
        "abstract": {"jazyk": "cs", "hodnotka": "jeeej"},
        "title": {"lang": "en", "value": "yaay"},
        "rights": [{"lang": "cs", "value": "jeeej"}, {"lang": "en", "value": "yeeey"}],
    }
