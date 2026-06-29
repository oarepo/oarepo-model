# Bug: PolymorphicField raises ValidationError on load, silently drops discriminator on dump, raises AssertionError for unknown types

## Affected version

`oarepo-model` v0.1.0dev50 (tag `v0.1.0dev50`).
**PR target:** upstream `main` (currently at v2.x after major bump #105).

## Summary

`PolymorphicField` has three related bugs in `_serialize` and `_deserialize`:

1. **Load raises `ValidationError: Unknown field`** — the full value dict (including
   the discriminator key) is passed to the sub-schema, which uses `unknown=RAISE`
   and does not declare the discriminator field.

2. **Dump silently drops the discriminator** — the sub-schema only serializes its
   declared fields, so the discriminator key is lost on every dump.  A subsequent
   load of the dumped value then fails because the discriminator is missing.

3. **Unknown discriminator raises `AssertionError`** — `self.fail('unknown_type', ...)`
   is called with a key not present in `error_messages`, which causes marshmallow
   to raise `AssertionError` internally instead of `ValidationError`.

## Steps to reproduce

```python
# 1. Load fails with ValidationError: Unknown field
schema.load({"field": {"kind": "type_a", "name": "Muenster"}})
# ValidationError: {'field': {'kind': ['Unknown field.']}}

# 2. Dump drops the discriminator
loaded = ... # dict with 'kind' key
dumped = schema.dump(loaded)
assert 'kind' in dumped['field']  # AssertionError — 'kind' missing

# 3. Unknown discriminator raises AssertionError
schema.load({"field": {"kind": "unknown_type", "name": "x"}})
# AssertionError (not ValidationError)
```

## Root cause

`_deserialize` passed the full `value` dict (discriminator included) to
`schema_field._deserialize()`.  `_serialize` did not put the discriminator back
after calling `schema_field._serialize()`.  `self.fail('unknown_type', ...)` used
a key not registered in `error_messages`.

## Proposed fix (this branch)

**Commit 1** — Strip the discriminator key from `value` before handing it to the
sub-schema on `_deserialize`; restore it in the returned dict.  Re-add the
discriminator to the serialized dict after the sub-schema dumps on `_serialize`.
Replace `self.fail()` with `raise ma.ValidationError(...)` directly, including
the list of valid types.

**Commit 2** — Add `preserve_discriminator` parameter (default `True`).  UI schemas
should not re-inject the discriminator; passing `preserve_discriminator=False` from
`PolymorphicDataType.create_marshmallow_field` preserves the previous UI behaviour.

**Commit 3** — Tests covering load, dump, round-trip, error paths, and
polymorphic-in-array.
