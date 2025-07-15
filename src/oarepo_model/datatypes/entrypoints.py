from .base import DataType
from .boolean import BooleanDataType
from .collections import ArrayDataType, NestedDataType, ObjectDataType
from .numbers import DoubleDataType, FloatDataType, IntegerDataType, LongDataType
from .strings import FullTextDataType, FulltextWithKeywordDataType, KeywordDataType

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
}
