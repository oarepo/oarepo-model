from typing import Any, override

import marshmallow.fields
import marshmallow_utils.fields 
import marshmallow.validate
from marshmallow_utils.fields.edtfdatestring import EDTFValidator
import edtf 
import functools


from datetime import datetime

from .base import DataType

class DateDataType(DataType):
    TYPE = "date"
    
    marshmallow_field_class = marshmallow.fields.Date
    jsonschema_type = {"type": "string", "format": "date"}
    mapping_type = {"type": "date", "format": "basic_date||strict_date"}
    
    @override
    def create_ui_marshmallow_fields(self, field_name: str, element: dict[str, Any]) -> dict[str, marshmallow.fields.Field]:
        """
        Create a Marshmallow UI fields for Date value, specifically long, medium, short, full formats.
        """
        return {
            f'{field_name}_l10n_long': marshmallow_utils.fields.FormatDate(attribute=field_name, format="long"),
            f'{field_name}_l10n_medium': marshmallow_utils.fields.FormatDate(attribute=field_name, format="medium"),
            f'{field_name}_l10n_short': marshmallow_utils.fields.FormatDate(attribute=field_name, format="short"),
            f'{field_name}_l10n_full': marshmallow_utils.fields.FormatDate(attribute=field_name, format="full"),
    }
    
    @override      
    def _get_marshmallow_field_args(self, field_name, element):
        ret = super()._get_marshmallow_field_args(field_name, element)
           
        min_date = element.get("min_date")
        max_date = element.get("max_date")
        if min_date or max_date:
            ret.setdefault("validate", []).append(
                marshmallow.validate.Range(min=min_date, max=max_date)
            )

        return ret  
    
class DateTimeDataType(DataType):
    TYPE = "datetime"

    marshmallow_field_class = marshmallow.fields.DateTime
    jsonschema_type = {"type": "string", "format": "date-time"}
    mapping_type = {
        "type": "date",
        "format": "strict_date_time||strict_date_time_no_millis||basic_date_time||basic_date_time_no_millis||basic_date||strict_date||strict_date_hour_minute_second||strict_date_hour_minute_second_fraction",
    }

    @override
    def create_ui_marshmallow_fields(self, field_name: str, element: dict[str, Any]) -> dict[str, marshmallow.fields.Field]:
        """
        Create a Marshmallow UI fields for DateTime value, specifically long, medium, short, full formats.
        """            
        return {
            f'{field_name}_l10n_long': marshmallow_utils.fields.FormatDatetime(attribute=field_name, format="long"),
            f'{field_name}_l10n_medium': marshmallow_utils.fields.FormatDatetime(attribute=field_name, format="medium"),
            f'{field_name}_l10n_short': marshmallow_utils.fields.FormatDatetime(attribute=field_name, format="short"),
            f'{field_name}_l10n_full': marshmallow_utils.fields.FormatDatetime(attribute=field_name, format="full"),
    }
    
    @override
    def _get_marshmallow_field_args(
        self, field_name: str, element: dict[str, Any]
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
        
        min_dt = element.get("min_datetime")
        max_dt = element.get("max_datetime")
        if min_dt or max_dt:
            ret.setdefault("validate", []).append(
                marshmallow.validate.Range(min=min_dt, max=max_dt)
            )

        return ret   
    
class TimeDataType(DataType):
    TYPE = "time"

    marshmallow_field_class = marshmallow.fields.Time
    jsonschema_type = {"type": "string", "format": "time"}
    mapping_type = {
        "type": "date",
        "format": "strict_time||strict_time_no_millis||basic_time||basic_time_no_millis||hour_minute_second||hour||hour_minute",
    } 
    
    @override
    def create_ui_marshmallow_fields(self, field_name: str, element: dict[str, Any]) -> dict[str, marshmallow.fields.Field]:
        """
        Create a Marshmallow UI fields for Time value, specifically long, medium, short, full formats.
        """
                
        return {
            f'{field_name}_l10n_long': marshmallow_utils.fields.FormatTime(attribute=field_name, format="long"),
            f'{field_name}_l10n_medium': marshmallow_utils.fields.FormatTime(attribute=field_name, format="medium"),
            f'{field_name}_l10n_short': marshmallow_utils.fields.FormatTime(attribute=field_name, format="short"),
            f'{field_name}_l10n_full': marshmallow_utils.fields.FormatTime(attribute=field_name, format="full"),
    }
    
    @override
    def _get_marshmallow_field_args(self, field_name: str, element: dict[str, Any]) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
    
        min_time = element.get("min_time")
        max_time = element.get("max_time")

        if min_time or max_time:
            ret.setdefault("validate", []).append(
                marshmallow.validate.Range(min=min_time, max=max_time)
            )
        return ret

class CachedMultilayerEDTFValidator(EDTFValidator):
    @functools.lru_cache(maxsize=1024)
    def __call__(self, value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except Exception:
            return super().__call__(value)

    
class EDTFTimeDataType(DataType):
    TYPE = "edtf-time"

    marshmallow_field_class = marshmallow_utils.fields.edtfdatestring.EDTFDateTimeString
    jsonschema_type = {"type": "string", "format": "date-time"}
    mapping_type = {
        "type": "date",
        "format": "strict_date_time||strict_date_time_no_millis||strict_date||yyyy-MM||yyyy",
    }

    @override
    def create_ui_marshmallow_fields(self, field_name: str, element: dict[str, Any]) -> dict[str, marshmallow.fields.Field]:
        """
        Create a Marshmallow UI fields for EDTFTime value, specifically long, medium, short, full formats.
        """            
        return {
            f'{field_name}_l10n_long': marshmallow_utils.fields.FormatEDTF(attribute=field_name, format="long"),
            f'{field_name}_l10n_medium': marshmallow_utils.fields.FormatEDTF(attribute=field_name, format="medium"),
            f'{field_name}_l10n_short': marshmallow_utils.fields.FormatEDTF(attribute=field_name, format="short"),
            f'{field_name}_l10n_full': marshmallow_utils.fields.FormatEDTF(attribute=field_name, format="full"),
    }    
    
    @override
    def _get_marshmallow_field_args(self, field_name: str, element: dict[str, Any]) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
        
        ret.setdefault('validate',[]).append(
            CachedMultilayerEDTFValidator(types=[edtf.DateAndTime, edtf.Date])
        ) 
            
        return ret


class EDTFDataType(DataType):
    TYPE = "edtf"

    marshmallow_field_class = marshmallow.fields.String
    jsonschema_type = {"type": "string", "format": "date"}
    mapping_type = {
        "type": "date",
        "format": "strict_date||yyyy-MM||yyyy",
    }
    
    @override
    def create_ui_marshmallow_fields(self, field_name: str, element: dict[str, Any]) -> dict[str, marshmallow.fields.Field]:
        """
        Create a Marshmallow UI fields for EDTF value, specifically long, medium, short, full formats.
        """
                
        return {
            f"{field_name}_l10n_long": marshmallow_utils.fields.FormatEDTF(attribute=field_name, format="long"),
            f"{field_name}_l10n_medium": marshmallow_utils.fields.FormatEDTF(attribute=field_name, format="medium"),
            f"{field_name}_l10n_short": marshmallow_utils.fields.FormatEDTF(attribute=field_name, format="short"),
            f"{field_name}_l10n_full": marshmallow_utils.fields.FormatEDTF(attribute=field_name, format="full"),
        }
                
    
    @override
    def _get_marshmallow_field_args(self, field_name: str, element: dict[str, Any]) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
       
        ret.setdefault('validate',[]).append(
            CachedMultilayerEDTFValidator(types=[edtf.Date])
        ) 
        
        return ret   

class EDTFIntervalType(DataType):
    TYPE = "edtf-interval"

    marshmallow_field_class = marshmallow.fields.String
    jsonschema_type = {"type": "string", "format": "date"}
    mapping_type = {
        "type": "date_range",
        "format": "strict_date||yyyy-MM||yyyy",
    }

    @override
    def create_ui_marshmallow_fields(self, field_name: str, element: dict[str, Any]) -> dict[str, marshmallow.fields.Field]:
        """
        Create a Marshmallow UI fields for EDTFInterval value, specifically long, medium, short, full formats.
        """
                
        return {
            f"{field_name}_l10n_long": marshmallow_utils.fields.FormatEDTF(attribute=field_name, format="long"),
            f"{field_name}_l10n_medium": marshmallow_utils.fields.FormatEDTF(attribute=field_name, format="medium"),
            f"{field_name}_l10n_short": marshmallow_utils.fields.FormatEDTF(attribute=field_name, format="short"),
            f"{field_name}_l10n_full": marshmallow_utils.fields.FormatEDTF(attribute=field_name, format="full"),
        }
        
    
    @override
    def _get_marshmallow_field_args(self, field_name: str, element: dict[str, Any]) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
        
        ret.setdefault('validate',[]).append(
            CachedMultilayerEDTFValidator(types=[edtf.Interval])
        ) 
        
        return ret 


    