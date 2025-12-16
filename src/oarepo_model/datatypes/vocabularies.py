#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Data type for controlled vocabulary references.

This module provides the VocabularyDataType class for creating references to
controlled vocabularies in OARepo models. It extends the PIDRelation data type
to handle vocabulary-specific functionality, including automatic field mapping
for different vocabulary types (affiliations, funders, awards, subjects) and
creation of appropriate Marshmallow schemas for validation and serialization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from .relations import PIDRelation

if TYPE_CHECKING:
    from invenio_records_resources.records.systemfields.pid import PIDFieldContext
    from invenio_vocabularies.records.systemfields.pid import VocabularyPIDFieldContext
    from marshmallow import Schema


class VocabularyDataType(PIDRelation):
    """A reference to a controlled vocabulary.

    Usage:
    ```yaml
    a:
        type: vocabulary
        vocabulary-type: languages
    ```

    As vocabulary inherits from RelationDataType, you can use parameters from
    relations as well, such as `keys`, `pid_field`, `cache_key`, etc.
    """

    TYPE = "vocabulary"
    def resolve_keys(self, element):
        ret: dict[str, Any] = {}
        keys = element.setdefault("keys", [])
        known_keys = set()
        for key in keys:
            if isinstance(key, str):
                known_keys.add(key)
            elif isinstance(key, dict):
                known_keys.update(key.keys())
            else:
                raise TypeError(f"Invalid key type: {type(key)}")

        # if 'id' is not in keys, add it as a keyword field
        if "id" not in known_keys:
            keys.append({"id": {"type": "keyword"}})

        # add other fields based on the vocabulary type
        vocabulary_fields = (
                default_vocabulary_fields_in_relations.get(element["vocabulary-type"])
                or default_vocabulary_fields_in_relations["*"]
        )
        for prop in vocabulary_fields:
            for key, value in prop.items():
                if key not in known_keys:
                    keys.append({key: value})
        for k in element['keys']:
            ret.update(k)

        if "id" not in ret:
            ret["id"] = {"type": "keyword"}
        # if @v is not in keys, add it as a keyword field, set marshmallow as dump only
        if "@v" not in ret:
            ret["@v"] = {"type": "keyword", "skip_marshmallow": True}
        return ret
    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        self.resolve_keys(element)

        return super()._get_properties(element)

    @override
    def create_marshmallow_schema(self, element: dict[str, Any]) -> type[Schema]:
        match element["vocabulary-type"]:
            case "affiliations":
                from invenio_vocabularies.contrib.affiliations.schema import (
                    AffiliationRelationSchema,
                )

                return cast("type[Schema]", AffiliationRelationSchema)
            case "funders":
                from invenio_vocabularies.contrib.funders.schema import (
                    FunderRelationSchema,
                )

                return cast("type[Schema]", FunderRelationSchema)
            case "awards":
                from invenio_vocabularies.contrib.awards.schema import (
                    AwardRelationSchema,
                )

                return cast("type[Schema]", AwardRelationSchema)
            case "subjects":
                from invenio_vocabularies.contrib.subjects.schema import (
                    SubjectRelationSchema,
                )

                return cast("type[Schema]", SubjectRelationSchema)
            case _generic:
                return super().create_marshmallow_schema(element)

    @override
    def _key_names(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> list[str]:
        return sorted(self.resolve_keys(element).keys())

    @override
    def _pid_field(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> PIDFieldContext:
        match element["vocabulary-type"]:
            case "affiliations":
                from invenio_vocabularies.contrib.affiliations.api import Affiliation

                return Affiliation.pid
            case "funders":
                from invenio_vocabularies.contrib.funders.api import Funder

                return Funder.pid
            case "awards":
                from invenio_vocabularies.contrib.awards.api import Award

                return Award.pid
            case "subjects":
                from invenio_vocabularies.contrib.subjects.api import Subject

                return Subject.pid
            case vocab_type:
                from invenio_vocabularies.records.api import Vocabulary

                return cast(
                    "PIDFieldContext",
                    cast("VocabularyPIDFieldContext", Vocabulary.pid).with_type_ctx(vocab_type),
                )

    def _cache_key(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> str | None:
        return super()._cache_key(element, path) or element["vocabulary-type"]


default_vocabulary_fields_in_relations: dict[str, list[dict[str, Any]]] = {
    "affiliations": [
        {
            "identifiers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "scheme": {"type": "keyword"},
                        "identifier": {"type": "keyword"},
                    },
                },
            },
        },
        {"name": {"type": "keyword"}},
    ],
    "funders": [
        {
            "identifiers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "scheme": {"type": "keyword"},
                        "identifier": {"type": "keyword"},
                    },
                },
            },
        },
        {"name": {"type": "keyword"}},
    ],
    "awards": [
        {"title": {"type": "i18ndict"}},
        {"number": {"type": "keyword"}},
        {
            "identifiers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "scheme": {"type": "keyword"},
                        "identifier": {"type": "keyword"},
                    },
                },
            },
        },
        {"acronym": {"type": "keyword"}},
        {"program": {"type": "keyword"}},
        {
            "subjects": {
                "type": "array",
                "items": {"type": "vocabulary", "vocabulary-type": "subjects"},
            },
        },
        {
            "organizations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "scheme": {"type": "keyword"},
                        "id": {"type": "keyword"},
                        "organization": {"type": "keyword"},
                    },
                },
            },
        },
    ],
    "subjects": [
        {"subject": {"type": "keyword"}},
        {"scheme": {"type": "keyword"}},
        {"props": {"type": "dynamic-object"}},
    ],
    "*": [{"title": {"type": "i18ndict"}}],
}
