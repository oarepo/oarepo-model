from .base import DataType
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
    EDTFIntervalType,
    EDTFTimeDataType,
    TimeDataType,
)
from .multilingual import I18nDictDataType
from .numbers import DoubleDataType, FloatDataType, IntegerDataType, LongDataType
from .polymorphic import PolymorphicDataType
from .relations import PIDRelation
from .strings import FullTextDataType, FulltextWithKeywordDataType, KeywordDataType
from .vocabularies import VocabularyDataType

DATA_TYPES: dict[str, type[DataType]] = {
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
}
