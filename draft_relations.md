# Passing a draft record into a PID relation

Analysis of what would need to change in `oarepo_model`'s `pid-relation`
datatype (and the underlying `invenio-records`/`invenio-records-resources`
relation machinery) to allow a relation field to point at a record that is
still a *draft* (not yet published), e.g. when creating a draft that
references another not-yet-published draft.

Relevant files:

- `src/oarepo_model/datatypes/relations.py` — `PIDRelation` datatype
- `src/oarepo_model/customizations/high_level/add_pid_relation.py` — `AddPIDRelation`
- `.venv/.../invenio_records_resources/records/systemfields/relations.py` — invenio's `PIDRelation` system field
- `.venv/.../invenio_records/systemfields/relations/relations.py` — `RelationBase`
- `.venv/.../invenio_records_resources/records/systemfields/pid.py` — `PIDField`/`PIDFieldContext`
- `.venv/.../invenio_pidstore/resolver.py` — `Resolver`
- `.venv/.../invenio_drafts_resources/records/api.py` — `Record`/`Draft` API classes

## How it works today

The chain for a `pid-relation` field is:

1. `PIDRelation._relation_pid_field` (`relations.py:196-216`) resolves
   `record_cls.pid` **once**, at model-build time, against whatever class is
   given in `record_cls:`/`pid_field:` in the YAML — always the *published*
   Record class. That returns a `PIDFieldContext`
   (invenio_records_resources `pid.py:49`) bound permanently to that one
   class.
2. That context is stored as `pid_field=` on the invenio-records-resources
   `PIDRelation` system field (`records/systemfields/relations.py`), which
   drives both `resolve()` and `parse_value()`.
3. `RelationBase.set_value` (invenio_records `relations.py:82-111`) is the
   gate: it calls `parse_value(value)` then requires
   `self.exists(store_value)`, i.e. `resolve(store_value) is not None`,
   **synchronously**, before the value is even allowed to be written into the
   record dict. Validation isn't deferred to commit time — it happens the
   moment you do `record.relations.foo = X`.

## Why passing a draft record breaks, concretely

**`parse_value`** (invenio_records_resources `PIDRelation.parse_value`):

```python
elif isinstance(value, self.pid_field.record_cls):
    pid = getattr(self.pid_field.attr_name)   # missing `value` as first arg — TypeError
```

This branch is upstream-broken (arity bug) — passing *any* record instance,
published or draft, currently raises `TypeError` rather than working. It's
effectively dead code today. `self.pid_field.record_cls` is also fixed to
the published class only, so even fixed, a `Draft` instance wouldn't pass
`isinstance` unless `Draft` is a subclass of that specific `record_cls` (it
is, per `invenio_drafts_resources.records.api.Draft(Record)`, but only if
`record_cls` was exactly that shared base — in the general PID-relation case
it's some *other* model's class, so this doesn't apply cross-model).

**`resolve`** (`PIDFieldContext.resolve`, `pid.py:61-83`, called with
defaults `registered_only=True`):

- `Resolver.resolve` (`invenio_pidstore/resolver.py`) raises
  `PIDUnregistered` if `pid.is_new()` — and
  `DraftRecordIdProviderV2.default_status_with_obj = PIDStatus.NEW`, so an
  unpublished draft's PID is exactly this status. Caught by the outer
  blanket `except Exception: return None` in invenio_records_resources'
  `PIDRelation.resolve`, silently turning into "doesn't exist."
- Even with `registered_only=False`, the resolver's
  `getter=self.record_cls.get_record` is bound to the *published* Record
  class from step 1, which queries the published-records table. A draft
  that was never published has no row there (it lives in the Draft's own
  model table) → `NoResultFound` → same silent `None`.

Net effect: `exists()` returns `False` for any draft-only target, so
`set_value` raises `InvalidRelationValue` before you even get to the
resolve-at-runtime/dereference/index concerns.

## What would need to change

1. **Fix/extend `parse_value`** in an oarepo-side subclass of
   invenio-records-resources' `PIDRelation` (can't patch upstream in place):
   correct the `getattr` bug, and accept
   `isinstance(value, (record_cls, draft_cls))`, pulling the id off
   `value.pid.pid_value`.
2. **Make the pid_field draft-aware.** `_relation_pid_field`
   (`relations.py:196`) currently returns a single-class-bound
   `PIDFieldContext`. It needs to build (or the YAML needs to supply) a
   resolver that:
   - calls the underlying resolver with `registered_only=False` so
     `NEW`-status PIDs aren't rejected outright, and
   - tries the published `record_cls.get_record` first, and on
     `NoResultFound`/`None`, falls back to
     `draft_cls.get_record(id_, with_deleted=True)`.

   This means adding a `draft_cls` (or a single `service`/pair-of-classes
   reference) to the `pid-relation` YAML schema, since today only one class
   is ever named.
3. **Wire the new pid_field/relation classes through `AddPIDRelation`**
   (`add_pid_relation.py`) — it currently instantiates invenio's stock
   `PIDRelation`/`PIDListRelation`/`PIDNestedListRelation` directly; these
   would need to become oarepo subclasses (same pattern as the existing
   `PIDArbitraryNestedListRelation` from `oarepo_runtime`) so the fixed
   `parse_value`/draft-aware `resolve` are actually used.
4. **Ordering caveat**, not code but a real constraint: since `set_value`
   validates by resolving *immediately*, the referenced draft must already
   have a `PersistentIdentifier` row (i.e. `Draft.create(...)` — which calls
   `PIDField.post_create` → assigns the PID — must have already run) before
   you can point another record's relation at it. You can't set the
   relation to a draft that hasn't been created/flushed yet.
5. Cache/session handling
   (`self.cache[id_] = obj; db.session.expunge(obj.model)`) needs no
   change — a Draft instance has `.model` too.
6. Once 1–3 are fixed, dereferencing (marshmallow `@v`, OpenSearch indexing
   of the relation's dumped properties) automatically benefits, since they
   all go through the same `resolve()`/cache path.

## Alternative worth considering

The codebase already has a precedent for sidestepping this exact problem —
`InternalRelationDataType` (`src/oarepo_model/datatypes/internal_relations.py`)
avoids PID resolution entirely for same-record references by using an
in-record lookup table instead. If what's actually needed is "a draft
referencing another still-uncommitted part of itself," that pattern is a
much smaller change than draft-aware PID resolution; if genuine
cross-record/cross-model draft-to-draft references are needed, the plan
above is what's required.
