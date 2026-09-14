# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Entry points registry for OARepo data types.

This module provides a centralized registry of all available data types that can be
discovered and used by the OARepo model system through entry points registration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .boolean import BooleanDataType
from .collections import (
    ArrayDataType,
    DynamicObjectDataType,
    NestedDataType,
    ObjectDataType,
)
from .date import (
    DateDataType,
    DateTimeDataType,
    EDTFDataType,
    EDTFDateOrIntervalDataType,
    EDTFIntervalType,
    EDTFTimeDataType,
    TimeDataType,
)
from .internal_relations import InternalRelationDataType
from .lazy_relations import LazyPIDRelation
from .multilingual import I18nDictDataType, MultilingualDataType
from .numbers import DoubleDataType, FloatDataType, IntegerDataType, LongDataType
from .polymorphic import PolymorphicDataType
from .relations import PIDRelation
from .spherical import GeoPointDataType, ICRSDataType
from .strings import FullTextDataType, FulltextWithKeywordDataType, KeywordDataType
from .vocabularies import VocabularyDataType

if TYPE_CHECKING:
    from .base import DataType

DATA_TYPES: dict[str, type[DataType] | dict[str, Any]] = {
    KeywordDataType.TYPE: KeywordDataType,
    FullTextDataType.TYPE: FullTextDataType,
    FulltextWithKeywordDataType.TYPE: FulltextWithKeywordDataType,
    ObjectDataType.TYPE: ObjectDataType,
    DoubleDataType.TYPE: DoubleDataType,
    FloatDataType.TYPE: FloatDataType,
    IntegerDataType.TYPE: IntegerDataType,
    LongDataType.TYPE: LongDataType,
    BooleanDataType.TYPE: BooleanDataType,
    NestedDataType.TYPE: NestedDataType,
    ArrayDataType.TYPE: ArrayDataType,
    DateDataType.TYPE: DateDataType,
    DateTimeDataType.TYPE: DateTimeDataType,
    TimeDataType.TYPE: TimeDataType,
    EDTFDataType.TYPE: EDTFDataType,
    EDTFIntervalType.TYPE: EDTFIntervalType,
    EDTFTimeDataType.TYPE: EDTFTimeDataType,
    PIDRelation.TYPE: PIDRelation,
    VocabularyDataType.TYPE: VocabularyDataType,
    I18nDictDataType.TYPE: I18nDictDataType,
    DynamicObjectDataType.TYPE: DynamicObjectDataType,
    PolymorphicDataType.TYPE: PolymorphicDataType,
    EDTFDateOrIntervalDataType.TYPE: EDTFDateOrIntervalDataType,
    GeoPointDataType.TYPE: GeoPointDataType,
    ICRSDataType.TYPE: ICRSDataType,
    LazyPIDRelation.TYPE: LazyPIDRelation,
    InternalRelationDataType.TYPE: InternalRelationDataType,
    MultilingualDataType.TYPE: MultilingualDataType,
    "i18n": {
        "type": "object",
        "properties": {
            "lang": {
                "type": "vocabulary",
                "vocabulary-type": "languages",
                "searchable": False,
            },
            "value": {"type": "keyword", "searchable": False},
        },
    },
}
