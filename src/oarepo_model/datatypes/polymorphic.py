from __future__ import annotations

from typing import Any, override

import marshmallow as ma
from invenio_base.utils import obj_or_import_string

from .base import DataType


class PolymorhicDataType(DataType):
    """
    Data type for handling polymorphic schemas with discriminator fields.
    This allows for fields that can be one of several different types based on a discriminator field.
    """
    
    TYPE = "polymorphic"
    
    def __init__(self, registry, name = None):
        super().__init__(registry, name)
        self.discriminator: str = "type"
        self.oneof_schemas: list[dict[str, Any]] = []
        self.polymorphic_children: dict[str, DataType] = {}
    
    @override
    def create_marshmallow_field(self, field_name, element) -> ma.fields.Field:
        """
        Create a Marshmallow field for polymorphic data type.
        Uses OneOf field with different schemas based on discriminator.
        """
        
        if element.get("marshmallow_field") is not None:
            return obj_or_import_string(element["marshmallow_field"])
        
        # get discriminator field name and oneof schemas
        self.discriminator = element.get("discriminator", "type") 
        self.oneof_schemas = element.get("oneof", [])
        
        # create child data types for each oneof schema
        for oneof_item in self.oneof_schemas:
            discriminator_value = oneof_item.get("discriminator")
            schema_type = oneof_item.get("type")
            
            if discriminator_value and schema_type:
                schema_def = self._registry.get_type(schema_type)
                self.polymorphic_children[discriminator_value] = schema_def
        
        # create a custom polymorphic field        
        return PolymorphicField(
            discriminator=self.discriminator,
            schemas=self._create_schema_fields(field_name, element),
            **self._get_marshmallow_field_args(field_name, element)
        )
    
    def _create_schema_fields(
        self, field_name: str, element: dict[str, Any]
    ) -> dict[str, ma.fields.Field]:
        """
        Create marshmallow fields for each schema variant.
        """
        
        schema_fields = {}
        
        for oneof_item in self.oneof_schemas:
            discriminator_value = oneof_item.get("discriminator")
            
            if discriminator_value in self.polymorphic_children:
                child_datatype = self.polymorphic_children[discriminator_value]
                schema_fields[discriminator_value] = child_datatype.create_marshmallow_field(
                    field_name=discriminator_value, 
                    element={}
                )
                     
        return schema_fields        
    
    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        """
        Create JSON schema for polymorphic type using oneOf.
        """
        discriminator = element.get("discriminator", "type")
        oneof_schemas = element.get("oneof", [])
        
        json_one_of_schemas = []
        
        for oneof_item in oneof_schemas:
            discriminator_value = oneof_item.get("discriminator")
            schema_type = oneof_item.get("type")
            
            if discriminator_value and schema_type:
                schema = self._registry.get_type(schema_type)
                child_jsonschema = schema.create_json_schema(oneof_item)
                
                if "properties" not in child_jsonschema:
                    child_jsonschema["properties"] = {}

                child_jsonschema["properties"][discriminator] = {
                    "type": "string",
                    "const": discriminator_value
                }
                
                if "required" not in child_jsonschema:
                    child_jsonschema["required"] = []
                if discriminator not in child_jsonschema["required"]:
                    child_jsonschema["required"].append(discriminator)
                
                json_one_of_schemas.append(child_jsonschema)
        
        return {
            "oneOf": json_one_of_schemas,
            "discriminator": {
                "propertyName": discriminator
            }
        }         
    
    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        """
        Create a mapping for the data type.
        Uses object type with properties from all possible schemas.
        """
        discriminator = element.get("discriminator", "type")
        oneof_schemas = element.get("oneof", [])

        all_properties = {
            discriminator: {
                "type": "keyword"
            }
        }
        
        for oneof_item in oneof_schemas:
            discriminator_value = oneof_item.get("discriminator")
            schema_type = oneof_item.get("type")
            
            if discriminator_value and schema_type:
                schema = self._registry.get_type(schema_type)
                child_mapping = schema.create_mapping(oneof_item)
               
                if "properties" in child_mapping:
                    all_properties.update(child_mapping["properties"])
                    
        return {
            "type": "object",
            "properties": all_properties
        }             
        
        
        
class PolymorphicField(ma.fields.Field):
    def __init__(self, discriminator: str, schemas: dict[str, ma.fields.Field], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.discriminator = discriminator
        self.schemas = schemas
    
    def _serialize(self, value: Any, attr: str, obj: Any, **kwargs) -> Any:
        if not isinstance(value, dict):
            return value
        
        discriminator_value = value.get(self.discriminator)
        if discriminator_value in self.schemas:
            schema_field = self.schemas[discriminator_value]
            return schema_field._serialize(value, attr, obj, **kwargs)
        
        return value    
    
    def _deserialize(self, value, attr, data, **kwargs):
        discriminator_value = value.get(self.discriminator)
        
        if discriminator_value not in self.schemas:
            self.fail('unknown_type', type=discriminator_value)
            
        schema_field = self.schemas[discriminator_value]
        return schema_field._deserialize(value, attr, data, **kwargs)   
                
    