#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Date and time data types for OARepo models.

This module provides date and time related data types including basic dates,
date ranges, date intervals, and EDTF (Extended Date/Time Format) support
for use in OARepo models.
"""

from __future__ import annotations

import functools
from datetime import datetime
from types import MappingProxyType
from typing import Any, override

import edtf
import marshmallow.fields
import marshmallow.validate
import marshmallow_utils.fields
from marshmallow_utils.fields.edtfdatestring import EDTFValidator

from .base import DataType, FacetMixin


class DateDataType(FacetMixin, DataType):
    """Data type for basic date values."""

    TYPE = "date"

    marshmallow_field_class = marshmallow.fields.Date
    jsonschema_type = MappingProxyType({"type": "string", "format": "date"})
    mapping_type = MappingProxyType(
        {"type": "date", "format": "basic_date||strict_date"},
    )

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a Marshmallow UI fields for Date value, specifically long, medium, short, full formats."""
        return {
            f"{field_name}_l10n_long": marshmallow_utils.fields.FormatDate(
                attribute=field_name,
                format="long",
            ),
            f"{field_name}_l10n_medium": marshmallow_utils.fields.FormatDate(
                attribute=field_name,
                format="medium",
            ),
            f"{field_name}_l10n_short": marshmallow_utils.fields.FormatDate(
                attribute=field_name,
                format="short",
            ),
            f"{field_name}_l10n_full": marshmallow_utils.fields.FormatDate(
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

    marshmallow_field_class = marshmallow.fields.DateTime
    jsonschema_type = MappingProxyType({"type": "string", "format": "date-time"})
    mapping_type = MappingProxyType(
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
        return {
            f"{field_name}_l10n_long": marshmallow_utils.fields.FormatDatetime(
                attribute=field_name,
                format="long",
            ),
            f"{field_name}_l10n_medium": marshmallow_utils.fields.FormatDatetime(
                attribute=field_name,
                format="medium",
            ),
            f"{field_name}_l10n_short": marshmallow_utils.fields.FormatDatetime(
                attribute=field_name,
                format="short",
            ),
            f"{field_name}_l10n_full": marshmallow_utils.fields.FormatDatetime(
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

    marshmallow_field_class = marshmallow.fields.Time
    jsonschema_type = MappingProxyType({"type": "string", "format": "time"})
    mapping_type = MappingProxyType(
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
        return {
            f"{field_name}_l10n_long": marshmallow_utils.fields.FormatTime(
                attribute=field_name,
                format="long",
            ),
            f"{field_name}_l10n_medium": marshmallow_utils.fields.FormatTime(
                attribute=field_name,
                format="medium",
            ),
            f"{field_name}_l10n_short": marshmallow_utils.fields.FormatTime(
                attribute=field_name,
                format="short",
            ),
            f"{field_name}_l10n_full": marshmallow_utils.fields.FormatTime(
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


class CachedMultilayerEDTFValidator(EDTFValidator):
    """A cached EDTF validator."""

    @override
    def __call__(self, value: str) -> str:
        """Validate the EDTF value and return it."""
        return self._cached_validation(value)

    @functools.lru_cache(maxsize=1024)  # noqa memory consumption ok
    def _cached_validation(self, value: str) -> str:
        """Validate EDTF string.

        If a value is valid, do not revalidate again, take it from cache.
        """
        # at first try to parse the value as a date because it is much faster
        # and most of the time it is a date
        try:
            datetime.strptime(value, "%Y-%m-%d")  # noqa naive datetime ok here
        except Exception:  # noqa catching all exceptions is ok here
            value = super().__call__(value)
        return value


class EDTFTimeDataType(FacetMixin, DataType):
    """Data type for EDTF (Extended Date/Time Format) time values."""

    TYPE = "edtf-time"

    marshmallow_field_class = marshmallow_utils.fields.edtfdatestring.EDTFDateTimeString
    jsonschema_type = MappingProxyType({"type": "string", "format": "date-time"})
    mapping_type = MappingProxyType(
        {
            "type": "date",
            "format": "strict_date_time||strict_date_time_no_millis||strict_date||yyyy-MM||yyyy",
        },
    )

    @property
    def facet_name(self) -> str:
        """Define facet class."""
        return "oarepo_runtime.services.facets.date.EDTFFacet"

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a Marshmallow UI fields for EDTFTime value, specifically long, medium, short, full formats."""
        return {
            f"{field_name}_l10n_long": marshmallow_utils.fields.FormatEDTF(
                attribute=field_name,
                format="long",
            ),
            f"{field_name}_l10n_medium": marshmallow_utils.fields.FormatEDTF(
                attribute=field_name,
                format="medium",
            ),
            f"{field_name}_l10n_short": marshmallow_utils.fields.FormatEDTF(
                attribute=field_name,
                format="short",
            ),
            f"{field_name}_l10n_full": marshmallow_utils.fields.FormatEDTF(
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

        ret.setdefault("validate", []).append(
            CachedMultilayerEDTFValidator(types=[edtf.DateAndTime, edtf.Date]),
        )

        return ret


class EDTFDataType(FacetMixin, DataType):
    """Data type for EDTF (Extended Date/Time Format) values."""

    TYPE = "edtf"

    marshmallow_field_class = marshmallow.fields.String
    jsonschema_type = MappingProxyType({"type": "string", "format": "date"})
    mapping_type = MappingProxyType(
        {
            "type": "date",
            "format": "strict_date||yyyy-MM||yyyy",
        },
    )

    @property
    def facet_name(self) -> str:
        """Define facet class."""
        return "oarepo_runtime.services.facets.date.EDTFFacet"

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a Marshmallow UI fields for EDTF value, specifically long, medium, short, full formats."""
        return {
            f"{field_name}_l10n_long": marshmallow_utils.fields.FormatEDTF(
                attribute=field_name,
                format="long",
            ),
            f"{field_name}_l10n_medium": marshmallow_utils.fields.FormatEDTF(
                attribute=field_name,
                format="medium",
            ),
            f"{field_name}_l10n_short": marshmallow_utils.fields.FormatEDTF(
                attribute=field_name,
                format="short",
            ),
            f"{field_name}_l10n_full": marshmallow_utils.fields.FormatEDTF(
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

        ret.setdefault("validate", []).append(
            CachedMultilayerEDTFValidator(types=[edtf.Date]),
        )

        return ret


class EDTFIntervalType(DataType):
    """Data type for EDTF intervals."""

    TYPE = "edtf-interval"

    marshmallow_field_class = marshmallow.fields.String
    jsonschema_type = MappingProxyType({"type": "string", "format": "date"})
    mapping_type = MappingProxyType(
        {
            "type": "date_range",
            "format": "strict_date||yyyy-MM||yyyy",
        },
    )

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a Marshmallow UI fields for EDTFInterval value, specifically long, medium, short, full formats."""
        return {
            f"{field_name}_l10n_long": marshmallow_utils.fields.FormatEDTF(
                attribute=field_name,
                format="long",
            ),
            f"{field_name}_l10n_medium": marshmallow_utils.fields.FormatEDTF(
                attribute=field_name,
                format="medium",
            ),
            f"{field_name}_l10n_short": marshmallow_utils.fields.FormatEDTF(
                attribute=field_name,
                format="short",
            ),
            f"{field_name}_l10n_full": marshmallow_utils.fields.FormatEDTF(
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

        ret.setdefault("validate", []).append(
            CachedMultilayerEDTFValidator(types=[edtf.Interval]),
        )

        return ret

    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any] | None = None,
        facets: dict[str, list] | None = None,
    ) -> Any:
        """Create facets for the data type."""
        _, _, _, _ = path, element, nested_facets, facets
        return facets
