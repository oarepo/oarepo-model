# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Multilingual text data types: ``multilingual`` and ``i18ndict``.

Two ways to store text in several languages:

- ``multilingual`` - a list of ``{lang, value}`` entries (the ``i18n`` type), where
  ``lang`` references the languages vocabulary. At most one entry per language;
  duplicates are rejected. Accepts ``min_items`` and ``max_items``. Use it for
  metadata fields such as titles and descriptions.
- ``i18ndict`` - a plain dictionary keyed by language code, e.g.
  ``{"en": "Hello", "cs": "Ahoj"}``. Compact, but has no validation options (the
  marshmallow field is fixed). The UI serialization adds ``<field>_l10n`` with the
  text in the current locale, falling back to the default locale, then English,
  then any language.

Neither type generates facets for its sub-fields.

Example (model YAML):

```yaml
description:
  type: multilingual
title_translations:
  type: i18ndict
```

Valid input:

```json
{
  "description": [
    {"lang": {"id": "en"}, "value": "A dataset"},
    {"lang": {"id": "cs"}, "value": "Datová sada"}
  ],
  "title_translations": {"en": "Hello", "cs": "Ahoj"}
}
```

See https://nrp-cz.github.io/docs/customize/model_backend/model_reference#multilingual
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_i18n import get_locale
from invenio_vocabularies.resources.serializer import current_default_locale
from invenio_vocabularies.services.schema import i18n_strings
from marshmallow import ValidationError
from marshmallow_utils.fields import BabelGettextDictField

from .collections import ArrayDataType, NoItemsError, ObjectDataType

if TYPE_CHECKING:
    import marshmallow


def multilingual_validator(data: list) -> None:
    """Validate language uniqueness."""
    seen = []
    for mult in data:
        lang = mult["lang"]["id"]
        if lang not in seen:
            seen.append(lang)
        else:
            raise ValidationError(f"Duplicated language code {lang}.")


class MultilingualDataType(ArrayDataType):
    """A data type for multilingual fields: an array of i18n entries ({lang, value}).

    Registered directly as "multilingual" - unlike the i18n entry, no wrapper
    dict with a separate impl key is needed, because the default item
    definition is supplied by ``_get_items`` below.
    """

    TYPE = "multilingual"

    @override
    def _get_items(self, element: dict[str, Any]) -> dict[str, Any]:
        """Return the declared items, defaulting to an i18n entry definition."""
        try:
            return super()._get_items(element)
        except NoItemsError:
            return {"type": "i18n"}

    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        field_args = super()._get_marshmallow_field_args(field_name, element)

        field_args.setdefault("validate", []).append(multilingual_validator)
        return field_args


class I18nDictL10NField(BabelGettextDictField):
    """The i18ndict value in the current locale (falling back to BABEL_DEFAULT_LOCALE, "en", then any)."""

    def __init__(self, **kwargs: Any) -> None:
        """Look up the current locale, falling back to the app's default locale."""
        super().__init__(get_locale, current_default_locale, **kwargs)

    @override
    def _serialize(self, value: Any, attr: str | None, obj: Any, **kwargs: Any) -> Any:
        # the parent crashes on an empty dict (it picks "the first translation")
        return super()._serialize(value, attr, obj, **kwargs) if value else None


class I18nDictDataType(ObjectDataType):
    """A data type for multilingual dictionaries.

    Their serialization is:
    {
        "en": "English text",
        "fi": "Finnish text",
        ...
    }
    """

    TYPE = "i18ndict"

    @override
    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        """Get properties for the data type."""
        # Note: maybe we should allow defining properties, not a strong need for now
        return {}

    @override
    def create_marshmallow_field(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> marshmallow.fields.Field:
        """Create a Marshmallow field for the data type.

        This method should be overridden by subclasses to provide specific field creation logic.
        """
        return i18n_strings

    @override
    def create_ui_marshmallow_fields(self, field_name: str, element: dict[str, Any]) -> dict[str, Any]:
        """Add ``<field_name>_l10n`` with the value in the current locale (as vocabulary ``title_l10n``)."""
        return {f"{field_name}_l10n": I18nDictL10NField(attribute=field_name)}

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create a JSON schema for the data type.

        This method should be overridden by subclasses to provide specific JSON schema creation logic.
        """
        return {"type": "object", "additionalProperties": {"type": "string"}}

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create a mapping for the data type.

        This method can be overridden by subclasses to provide specific mapping creation logic.
        """
        return {"type": "object", "dynamic": "true"}
