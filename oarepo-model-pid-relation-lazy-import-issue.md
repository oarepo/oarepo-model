# Bug: pid-relation build fails with ImportError / None for cross-module or self-referential record classes

## Affected version

`oarepo-model` v0.1.0dev50 (tag `v0.1.0dev50`).
**PR target:** upstream `main` (currently at v2.x after major bump #105).

## Summary

`PIDRelation._pid_field()` called `obj_or_import_string()` eagerly at model
construction time and returned the fully resolved `PIDFieldContext`.  When a
pid-relation references a record class that lives in a different module which
has not yet been imported — including self-referential relations where the
target is the same module currently being constructed — Python's import
machinery either raises `ImportError` or returns `None`, and the build fails
before any records can be loaded.

## Steps to reproduce

1. Define two record models in separate modules, each with a pid-relation
   pointing at the other (or a single model with a pid-relation pointing at
   itself, e.g. a `parent_activity` field).
2. Import either module.

**Result:** `ImportError: cannot import name '...'` or `ValueError: Record
class ... does not have a 'pid' attribute` raised at import time before the
Flask application is running.

## Root cause

`PIDRelation._pid_field()` in `src/oarepo_model/datatypes/relations.py`
resolves the `record_cls` or `pid_field` string via `obj_or_import_string()`
and immediately returns the live object.  Model files are imported during
Python module initialization; the target class is not yet available.

## Fix (this branch)

**Commit 1 — Defer resolution to `apply()`-time** (`relations.py`,
`add_pid_relation.py`): `_pid_field()` now returns a zero-argument callable.
`AddPIDRelation.apply()` receives the factory and resolves it (or wraps it in
a `LazyPIDFieldProxy`) before passing the result to `PIDRelation` /
`PIDListRelation` / `PIDArbitraryNestedListRelation`.  A pre-resolved value
(not callable) is still accepted for backward compatibility.

**Commit 2 — `LazyPIDFieldProxy` for truly deferred resolution**
(`add_pid_relation.py`): Even at `apply()`-time the same module may not be
fully initialized for self-referential models.  A proxy object stores the
factory and only calls it on first attribute access (at record I/O time),
when all modules are guaranteed loaded.

**Commit 3 — Tests** (`tests/datatypes/test_pid_relation_lazy_import.py`):
Covers the lazy-callable contract, error paths (bad module, missing keys),
`create_relations()` not importing at call time, and `AddPIDRelation`
backward compatibility.
