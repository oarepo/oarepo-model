#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import pytest
from invenio_records.systemfields.relations.errors import InvalidRelationValue
from marshmallow.exceptions import ValidationError


def test_multilingual(
    app,
    identity_simple,
    empty_model,
    multilingual_model,
    vocabulary_fixtures,
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
                "title": {
                    "lang": {
                        "id": "en",
                    },
                    "value": "yaay",
                },
                "abstract": {
                    "lang": {
                        "id": "cs",
                    },
                    "value": "jeeej",
                },
                "rights": [
                    {
                        "lang": {
                            "id": "cs",
                        },
                        "value": "jeeej",
                    },
                    {
                        "lang": {
                            "id": "en",
                        },
                        "value": "yeeey",
                    },
                ],
            },
        },
    )

    md = vocabulary_rec.data["metadata"]

    assert md == {
        "abstract": {
            "lang": {"id": "cs", "title": {"cs": "Čeština", "en": "Czech"}},
            "value": "jeeej",
        },
        "rights": [
            {
                "lang": {"id": "cs", "title": {"cs": "Čeština", "en": "Czech"}},
                "value": "jeeej",
            },
            {
                "lang": {"id": "en", "title": {"cs": "Angličtina", "en": "English"}},
                "value": "yeeey",
            },
        ],
        "title": {
            "lang": {"id": "en", "title": {"cs": "Angličtina", "en": "English"}},
            "value": "yaay",
        },
    }
    with pytest.raises(InvalidRelationValue):
        record_with_vocabulary_service.create(
            identity_simple,
            {
                "files": {
                    "enabled": False,
                },
                "metadata": {
                    "title": {
                        "lang": {
                            "id": "ww",
                        },
                        "value": "yaay",
                    }
                },
            },
        )

    with pytest.raises(InvalidRelationValue):
        record_with_vocabulary_service.create(
            identity_simple,
            {
                "files": {
                    "enabled": False,
                },
                "metadata": {
                    "title": {
                        "lang": {
                            "id": "",
                        },
                        "value": "yaay",
                    }
                },
            },
        )
    with pytest.raises(ValidationError):
        record_with_vocabulary_service.create(
            identity_simple,
            {
                "files": {
                    "enabled": False,
                },
                "metadata": {
                    "rights": [
                        {
                            "lang": {
                                "id": "cs",
                                "title": {"cs": "Čeština", "en": "Czech"},
                            },
                            "value": "jeeej",
                        },
                        {
                            "lang": {
                                "id": "cs",
                                "title": {"cs": "Angličtina", "en": "English"},
                            },
                            "value": "yeeey",
                        },
                    ],
                },
            },
        )
