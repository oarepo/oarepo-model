from typing import Any, override

from invenio_i18n import gettext
import marshmallow

from .base import DataType

class FormatBoolean(marshmallow.fields.Field):
    """Helper class for formatting single values of booleans."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        
        yes = gettext("true")
        no = gettext("false")
        return yes if value else no

class BooleanDataType(DataType):
    TYPE = "boolean"

    marshmallow_field_class = marshmallow.fields.Boolean
    jsonschema_type = "boolean"
    mapping_type = "boolean"

    @override
    def create_ui_marshmallow_fields(self, field_name: str, element: dict[str, Any]) -> dict[str, marshmallow.fields.Field]: 
        """
        Create a Marshmallow UI fields for Boolean value, specifically i18n format.
        """
        
        return {
           f"{field_name}_i18n": FormatBoolean(
                attribute=field_name,
            ) 
        }
    
    @override
    def _get_marshmallow_field_args(
        self, field_name: str, element: dict[str, Any]
    ) -> dict[str, Any]:
        ret = super()._get_marshmallow_field_args(field_name, element)
        ret["truthy"] = [True]
        ret["falsy"] = [False]
        return ret
