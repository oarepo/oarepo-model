from __future__ import annotations

from typing import TYPE_CHECKING, Any

from marshmallow.schema import Schema

from .relations import PIDRelation

if TYPE_CHECKING:
    pass


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

    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        keys = element.setdefault("keys", [])
        known_keys = set()
        for key in keys:
            if isinstance(key, str):
                known_keys.add(key)
            elif isinstance(key, dict):
                known_keys.update(key.keys())
            else:
                raise ValueError(f"Invalid key type: {type(key)}")

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

        return super()._get_properties(element)

    def create_marshmallow_schema(self, element: dict[str, Any]) -> type[Schema]:
        match element["vocabulary-type"]:
            case "affiliations":
                from invenio_vocabularies.contrib.affiliations.schema import (
                    AffiliationRelationSchema,
                )

                return AffiliationRelationSchema
            case "funders":
                from invenio_vocabularies.contrib.funders.schema import (
                    FunderRelationSchema,
                )

                return FunderRelationSchema
            case "awards":
                from invenio_vocabularies.contrib.awards.schema import (
                    AwardRelationSchema,
                )

                return AwardRelationSchema
            case "subjects":
                from invenio_vocabularies.contrib.subjects.schema import (
                    SubjectRelationSchema,
                )

                return SubjectRelationSchema
            case _generic:
                return super().create_marshmallow_schema(element)

    def _key_names(
        self, element: dict[str, Any], path: list[tuple[str, dict[str, Any]]]
    ) -> list[str]:
        return sorted(self._get_properties(element).keys())

    def _pid_field(
        self, element: dict[str, Any], path: list[tuple[str, dict[str, Any]]]
    ):
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

                return Vocabulary.pid.with_type_ctx(vocab_type)

    def _cache_key(
        self, element: dict[str, Any], path: list[tuple[str, dict[str, Any]]]
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
            }
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
            }
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
            }
        },
        {"acronym": {"type": "keyword"}},
        {"program": {"type": "keyword"}},
        {
            "subjects": {
                "type": "array",
                "items": {"type": "vocabulary", "vocabulary-type": "subjects"},
            }
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
            }
        },
    ],
    "subjects": [
        {"subject": {"type": "keyword"}},
        {"scheme": {"type": "keyword"}},
        {"props": {"type": "dynamic-object"}},
    ],
    "*": [{"title": {"type": "i18ndict"}}],
}
