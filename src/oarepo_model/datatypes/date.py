# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Date and time data types for OARepo models.

This module provides date and time related data types including basic dates,
date ranges, date intervals, and EDTF (Extended Date/Time Format) support
for use in OARepo models.
"""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING, Any, override

import edtf
import marshmallow.fields
import marshmallow.validate
import marshmallow_utils.fields
from marshmallow_utils.fields.edtfdatestring import EDTFValidator

from oarepo_model.utils import ReadOnlyDict

from .base import DataType, FacetMixin

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

from oarepo_runtime.services.schema.ui import (
    LocalizedEDTF,
    LocalizedEDTFTime,
    LocalizedEDTFTimeInterval,
)

_STRICT_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_STRICT_INTERVAL_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}/\d{4}-\d{2}-\d{2}$")


class KeepOriginalStringMixin(marshmallow.fields.Field):
    """Mixin schema to keep the original string value."""

    SERIALIZATION_FUNCS: Mapping[str, Callable] = {"iso": lambda val: val}

    @override
    def deserialize(
        self,
        value: Any,
        attr: str | None = None,
        data: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Deserialize the value and keep the original string."""
        super().deserialize(value, attr, data, **kwargs)
        return value  # return the original string if deserialization has not thrown an error


class DateString(KeepOriginalStringMixin, marshmallow.fields.Date):
    """Marshmallow field for date strings that keeps the original string."""


class DateTimeString(KeepOriginalStringMixin, marshmallow.fields.DateTime):
    """Marshmallow field for datetime strings that keeps the original string."""


class TimeString(KeepOriginalStringMixin, marshmallow.fields.Time):
    """Marshmallow field for time strings that keeps the original string."""


class DateDataType(FacetMixin, DataType):
    """Data type for basic date values."""

    TYPE = "date"

    marshmallow_field_class = DateString
    jsonschema_type = ReadOnlyDict({"type": "string", "format": "date"})
    mapping_type = ReadOnlyDict(
        {"type": "date", "format": "basic_date||strict_date"},
    )

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a Marshmallow UI fields for Date value, specifically long, medium, short, full formats."""
        field_class = self._get_ui_marshmallow_field_class(field_name, element) or marshmallow_utils.fields.FormatDate

        return {
            f"{field_name}_l10n_long": field_class(
                attribute=field_name,
                format="long",
            ),
            f"{field_name}_l10n_medium": field_class(
                attribute=field_name,
                format="medium",
            ),
            f"{field_name}_l10n_short": field_class(
                attribute=field_name,
                format="short",
            ),
            f"{field_name}_l10n_full": field_class(
                attribute=field_name,
                format="full",
            ),
        }

    @override
    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)

        min_date = element.get("min_date")
        max_date = element.get("max_date")
        if min_date or max_date:
            ret.setdefault("validate", []).append(
                marshmallow.validate.Range(min=min_date, max=max_date),
            )

        return ret

    @property
    def facet_name(self) -> str:
        """Define facet class."""
        return "oarepo_runtime.services.facets.date.DateFacet"


class DateTimeDataType(FacetMixin, DataType):
    """Data type for date and time values."""

    TYPE = "datetime"

    marshmallow_field_class = DateTimeString
    jsonschema_type = ReadOnlyDict({"type": "string", "format": "date-time"})
    mapping_type = ReadOnlyDict(
        {
            "type": "date",
            "format": "strict_date_time||strict_date_time_no_millis||basic_date_time||"
            "basic_date_time_no_millis||basic_date||strict_date||strict_date_hour_minute_second||"
            "strict_date_hour_minute_second_fraction",
        },
    )

    @property
    def facet_name(self) -> str:
        """Define facet class."""
        return "oarepo_runtime.services.facets.date.DateTimeFacet"

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a Marshmallow UI fields for DateTime value, specifically long, medium, short, full formats."""
        field_class = (
            self._get_ui_marshmallow_field_class(field_name, element) or marshmallow_utils.fields.FormatDatetime
        )
        return {
            f"{field_name}_l10n_long": field_class(
                attribute=field_name,
                format="long",
            ),
            f"{field_name}_l10n_medium": field_class(
                attribute=field_name,
                format="medium",
            ),
            f"{field_name}_l10n_short": field_class(
                attribute=field_name,
                format="short",
            ),
            f"{field_name}_l10n_full": field_class(
                attribute=field_name,
                format="full",
            ),
        }

    @override
    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)

        min_dt = element.get("min_datetime")
        max_dt = element.get("max_datetime")
        if min_dt or max_dt:
            ret.setdefault("validate", []).append(
                marshmallow.validate.Range(min=min_dt, max=max_dt),
            )

        return ret


class TimeDataType(FacetMixin, DataType):
    """Data type for time values."""

    TYPE = "time"

    marshmallow_field_class = TimeString
    jsonschema_type = ReadOnlyDict({"type": "string", "format": "time"})
    mapping_type = ReadOnlyDict(
        {
            "type": "date",
            "format": "strict_time||strict_time_no_millis||basic_time||"
            "basic_time_no_millis||hour_minute_second||hour||hour_minute",
        },
    )

    @property
    def facet_name(self) -> str:
        """Define facet class."""
        return "oarepo_runtime.services.facets.date.TimeFacet"

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a Marshmallow UI fields for Time value, specifically long, medium, short, full formats."""
        field_class = self._get_ui_marshmallow_field_class(field_name, element) or marshmallow_utils.fields.FormatTime
        return {
            f"{field_name}_l10n_long": field_class(
                attribute=field_name,
                format="long",
            ),
            f"{field_name}_l10n_medium": field_class(
                attribute=field_name,
                format="medium",
            ),
            f"{field_name}_l10n_short": field_class(
                attribute=field_name,
                format="short",
            ),
            f"{field_name}_l10n_full": field_class(
                attribute=field_name,
                format="full",
            ),
        }

    @override
    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)

        min_time = element.get("min_time")
        max_time = element.get("max_time")

        if min_time or max_time:
            ret.setdefault("validate", []).append(
                marshmallow.validate.Range(min=min_time, max=max_time),
            )
        return ret


def _strict_date(value: str) -> date | None:
    """Return the day ``value`` denotes as ``YYYY-MM-DD``, or None if it is not one."""
    if not _STRICT_DATE_PATTERN.match(value):
        return None
    try:
        return date(int(value[:4]), int(value[5:7]), int(value[8:10]))
    except ValueError:
        return None


class MultilayerEDTFValidator(EDTFValidator):
    """EDTF validator that decides strict level-0 input without running the grammar.

    ``parse_edtf`` is a pyparsing grammar and it dominates the cost of validating user
    input. A strict ``YYYY-MM-DD`` string, and an interval of two of them, always parse
    to the same EDTF object, so both can be decided by looking at the string - as long
    as the allowed ``types`` say what that object is accepted as.
    """

    @override
    def __call__(self, value: str) -> str:
        """Validate the EDTF value and return it."""
        if self._accepts_strict_value(value):
            return value
        return super().__call__(value)

    def _accepts_strict_value(self, value: Any) -> bool:
        """Whether ``value`` is a strict date/interval the configured types accept.

        The fast path has to reach the same verdict the full validation would: only the
        strict level-0 forms are matched, everything else (uncertainty, qualifyers,
        seasons, partial intervals, unspecified digits, ...) is left to the grammar.
        """
        if not isinstance(value, str):
            return False

        if "/" in value:
            if not _STRICT_INTERVAL_PATTERN.match(value):
                return False
            start = _strict_date(value[:10])
            end = _strict_date(value[11:])
            if start is None or end is None:
                return False
            # ISO dates of the same width compare chronologically, and an interval of
            # two dates fails the chronological check exactly when start > end.
            return start <= end and self._accepts(edtf.Interval)

        # a strict date parses to an edtf Date whose lower and upper bound are
        # identical, so it always passes the chronological check.
        return _strict_date(value) is not None and self._accepts(edtf.Date)

    def _accepts(self, parsed_type: type) -> bool:
        """Whether the configured ``types`` accept an object of ``parsed_type``."""
        return not self._types or any(issubclass(parsed_type, allowed) for allowed in self._types)


_EDTF_DATE_FORMATS = "strict_date||yyyy-MM||yyyy"


class EDTFBaseDataType(DataType):
    """Base for EDTF-based types, sharing the JSON schema, validators and l10n UI fields.

    Subclasses set ``TYPE``, ``mapping_type``, the accepted EDTF object types
    (``edtf_validator_types``) and the default UI field class
    (``default_ui_field_class``).
    """

    marshmallow_field_class = marshmallow.fields.String
    jsonschema_type = ReadOnlyDict({"type": "string", "format": "date"})

    edtf_validator_types: tuple[type, ...] = ()
    default_ui_field_class: type[marshmallow.fields.Field] = LocalizedEDTF

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a Marshmallow UI fields for the value, specifically long, medium, short, full formats."""
        field_class = self._get_ui_marshmallow_field_class(field_name, element) or self.default_ui_field_class
        return {
            f"{field_name}_l10n_{fmt}": field_class(
                attribute=field_name,
                format=fmt,
            )
            for fmt in ("long", "medium", "short", "full")
        }

    @override
    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
        if self.edtf_validator_types:
            ret.setdefault("validate", []).append(
                MultilayerEDTFValidator(types=list(self.edtf_validator_types)),
            )
        return ret


class EDTFTimeDataType(FacetMixin, EDTFBaseDataType):
    """Data type for EDTF (Extended Date/Time Format) time values."""

    TYPE = "edtf-time"

    marshmallow_field_class = marshmallow_utils.fields.edtfdatestring.EDTFDateTimeString
    jsonschema_type = ReadOnlyDict({"type": "string", "format": "date-time"})
    mapping_type = ReadOnlyDict(
        {
            "type": "date",
            "format": "strict_date_time||strict_date_time_no_millis||strict_date||yyyy-MM||yyyy",
        },
    )
    edtf_validator_types = (edtf.DateAndTime, edtf.Date)
    default_ui_field_class = LocalizedEDTFTime

    @property
    def facet_name(self) -> str:
        """Define facet class."""
        return "oarepo_runtime.services.facets.date.EDTFFacet"


class EDTFDataType(FacetMixin, EDTFBaseDataType):
    """Data type for EDTF (Extended Date/Time Format) values."""

    TYPE = "edtf"

    mapping_type = ReadOnlyDict(
        {
            "type": "date",
            "format": _EDTF_DATE_FORMATS,
        },
    )
    edtf_validator_types = (edtf.Date,)

    @property
    def facet_name(self) -> str:
        """Define facet class."""
        return "oarepo_runtime.services.facets.date.EDTFFacet"


class EDTFIntervalType(EDTFBaseDataType):
    """Data type for EDTF intervals."""

    TYPE = "edtf-interval"

    mapping_type = ReadOnlyDict(
        {
            "type": "date_range",
            "format": _EDTF_DATE_FORMATS,
        },
    )
    edtf_validator_types = (edtf.Interval,)
    default_ui_field_class = LocalizedEDTFTimeInterval


class EDTFDateOrIntervalDataType(EDTFBaseDataType):
    """An EDTF date or interval represented by keyword."""

    TYPE = "edtf-date-or-interval"

    mapping_type = ReadOnlyDict(
        {
            "type": "keyword",
        }
    )
    edtf_validator_types = (edtf.Date, edtf.Interval)
    default_ui_field_class = LocalizedEDTFTimeInterval

    @override
    def create_dynamic_mapping(self, field_name: str, element: dict[str, Any]) -> ReadOnlyDict:
        """Create RDM-style sibling date_range mapping."""
        _ = element
        return ReadOnlyDict(
            {
                f"{field_name}_range": {
                    "type": "date_range",
                },
            },
        )
