# Bug: DynamicObjectDataType.dump() always returns {} — stored data silently discarded

## Affected version

`oarepo-model` v0.1.0dev50 (tag `v0.1.0dev50`).
**PR target:** upstream `main` (currently at v2.x after major bump #105).

## Summary

`DynamicObjectDataType` inherits `ObjectDataType.create_marshmallow_field`, which
returns a `Nested` field wrapping a `PermissiveSchema`.  `PermissiveSchema` has no
declared fields, so `schema.dump()` always returns `{}`, silently discarding all
data stored in the field.  Loading works correctly (`unknown=INCLUDE` passes all
keys through), but the dump path is broken — any record with a `dynamic-object`
field loses that field's data on serialization.

## Steps to reproduce

```python
from oarepo_model.datatypes.collections import DynamicObjectDataType
import marshmallow as ma

# Create a DynamicObjectDataType field
dt = DynamicObjectDataType(...)
field = dt.create_marshmallow_field(field_name="data", element={"type": "dynamic-object"})
Schema = ma.Schema.from_dict({"data": field})

data = {"data": {"key": "value", "nested": {"x": 1}}}
loaded = Schema().load(data)   # {"data": {"key": "value", "nested": {"x": 1}}}
dumped = Schema().dump(loaded)  # {"data": {}}  ← bug: all content lost
```

## Root cause

`ObjectDataType.create_marshmallow_field` produces a `Nested` field wrapping
a `PermissiveSchema`.  `PermissiveSchema` is designed to accept arbitrary data
on load (`unknown=INCLUDE`) but declares no fields, so `ma.Schema.dump()` only
serializes declared fields — returning an empty dict.

`DynamicObjectDataType` does not override `create_marshmallow_field`, so it
inherits the broken behaviour.

## Impact

Any record type that uses `dynamic-object` fields (typically for storing
extensible or schema-less sub-documents) will silently lose that data on every
API response, export, or re-index operation.

## Proposed fix (this branch)

Override `create_marshmallow_field` in `DynamicObjectDataType` to return
`marshmallow.fields.Raw` instead of `Nested`.  `Raw` passes arbitrary JSON
through on both load and dump without transformation.  The base `DataType`
field args are used rather than `ObjectDataType`'s to avoid injecting the
`nested` kwarg, which is only meaningful for `Nested` and causes a marshmallow
warning on `Raw`.
