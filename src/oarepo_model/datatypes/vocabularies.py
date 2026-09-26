# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Data type for controlled vocabulary references.

This module provides the VocabularyDataType class for creating references to
controlled vocabularies in OARepo models. It extends the PIDRelation data type
to handle vocabulary-specific functionality, including automatic field mapping
for different vocabulary types (affiliations, funders, awards, subjects) and
creation of appropriate Marshmallow schemas for validation and serialization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from invenio_vocabularies.services.facets import VocabularyLabels

from .base import FacetMixin
from .relations import PIDRelation

if TYPE_CHECKING:
    from collections.abc import Mapping

    from invenio_records_resources.records.systemfields.pid import PIDFieldContext
    from invenio_vocabularies.records.systemfields.pid import VocabularyPIDFieldContext
    from marshmallow import Schema

    from oarepo_model.utils import ArrayPathMember


#: Vocabulary types that ship their own (invenio contrib) relation schema and
#: representation. They must not fall back to the generic ``{id, title_l10n}``
#: handling, as their stored shape differs (e.g. affiliations/funders use
#: ``name`` rather than ``title``).
SPECIALIZED_VOCABULARY_TYPES = ("affiliations", "funders", "awards", "subjects")


class VocabularyDataType(FacetMixin, PIDRelation):
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

    @override
    def _default_key_properties(self, element: dict[str, Any]) -> Mapping[str, dict[str, Any]]:
        """Vocabulary-type-specific default fields, plus a searchable 'id'.

        Unlike a generic PIDRelation (whose target may be an unresolvable
        still-building self-reference, see PIDRelation._default_key_properties),
        a vocabulary's target type is always known synchronously, so 'id' is
        safe to make searchable/facetable here - that's why it is overriden here.
        """
        vocabulary_fields = (
            default_vocabulary_fields_in_relations.get(element["vocabulary-type"])
            or default_vocabulary_fields_in_relations["*"]
        )
        return {
            **super()._default_key_properties(element),
            **{key: value for prop in vocabulary_fields for key, value in prop.items()},
            "id": {"type": "keyword"},
        }

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
    def create_ui_marshmallow_schema(self, element: dict[str, Any]) -> type[Schema]:
        # The generic i18ndict UI serialization is not implemented yet (returns {}),
        # so without this a vocabulary reference would emit an empty `ui` block.
        # Emit the standard {id, title_l10n} UI representation for *generic* vocabularies.
        # For specialized contrib vocabularies, keep the existing UI serialization behavior.
        if element["vocabulary-type"] in SPECIALIZED_VOCABULARY_TYPES:
            return super().create_ui_marshmallow_schema(element)

        from invenio_vocabularies.resources.schema import VocabularyL10Schema

        return cast("type[Schema]", VocabularyL10Schema)

    @override
    def _relation_key_names(
        self,
        element: dict[str, Any],
        path: list[ArrayPathMember],
    ) -> list[str]:
        names = self._key_names(element.get("keys", [])) | self._default_key_properties(element).keys()
        return sorted(names)

    @override
    def _relation_pid_field(
        self,
        element: dict[str, Any],
        path: list[ArrayPathMember],
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

    @override
    def _relation_cache_key(
        self,
        element: dict[str, Any],
        path: list[ArrayPathMember],
    ) -> str | None:
        return super()._relation_cache_key(element, path) or element["vocabulary-type"]

    @override
    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
        path_suffix: str = "",
        ignored_keys: set[str] | None = None,
    ) -> Any:
        # MRO puts FacetMixin before PIDRelation (see class VocabularyDataType
        # bases below), so super() here is FacetMixin.get_facet - a leaf
        # implementation that produces a single facet for this vocabulary
        # reference itself (not a recursive property walk), and has no
        # 'ignored_keys' concept to forward to.
        return super().get_facet(
            path,
            element,
            nested_facets,
            facets,
            path_suffix=path_suffix or ".id",
        )

    @override
    def _get_facet_kwargs(
        self,
        path: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        vocabulary_type = element["vocabulary-type"]

        if vocabulary_type in {"affiliations", "funders"}:
            return {
                "value_labels": VocabularyLabels(
                    vocabulary_type,
                    service_id=vocabulary_type,
                ),
            }

        return {"value_labels": VocabularyLabels(vocabulary_type)}


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
