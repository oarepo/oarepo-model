# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

import importlib
import importlib.resources
import json
import sys
from importlib.util import find_spec

import pytest

from oarepo_model.api import model
from oarepo_model.presets.records_resources import records_resources_preset

MODEL_TYPES = [
    {
        "Metadata": {
            "properties": {
                "title": {"type": "fulltext+keyword", "required": True},
            },
        },
    },
]


def build_model(name: str):
    """Build a model with the records_resources preset and no customizations."""
    return model(
        name=name,
        version="1.0.0",
        presets=[records_resources_preset],
        types=MODEL_TYPES,
        metadata_type="Metadata",
    )


def model_module_names(name: str) -> list[str]:
    """Return all sys.modules entries belonging to the given runtime model."""
    prefix = f"runtime_models_{name}"
    return [n for n in sys.modules if n == prefix or n.startswith(f"{prefix}.")]


def test_unregister_purges_imported_modules_and_is_idempotent():
    m1 = build_model("unregister_roundtrip")
    m1.register()
    pkg = "runtime_models_unregister_roundtrip"
    root1 = importlib.import_module(pkg)
    assert root1.Record is m1.Record
    importlib.import_module(f"{pkg}.jsonschemas")
    importlib.import_module(f"{pkg}.mappings")
    assert len(model_module_names("unregister_roundtrip")) >= 3

    m1.unregister()

    # all modules of the model were purged from sys.modules, and importing
    # fails now that the importer is gone from sys.meta_path
    assert model_module_names("unregister_roundtrip") == []
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(pkg)

    # idempotent - unregistering an already unregistered model is a no-op
    m1.unregister()

    # re-registering imports a fresh module: a new module object, re-executed
    # from the current namespace - not the stale module cached before
    m1.Marker = object()
    m1.register()
    root2 = importlib.import_module(pkg)
    assert root2 is not root1
    assert root2.Marker is m1.Marker
    assert root2.Record is m1.Record
    m1.unregister()

    assert model_module_names("unregister_roundtrip") == []


def test_unregister_unregistered_model_is_a_noop():
    m = build_model("unregister_never_registered")
    m.unregister()
    assert model_module_names("unregister_never_registered") == []


def find_schema_file(root):
    """Return the first jsonschema file traversable under the model's jsonschemas dir."""
    jsonschemas = next(c for c in root.iterdir() if c.name == "jsonschemas")
    return next(c for c in jsonschemas.iterdir() if c.name.endswith(".json"))


def test_traversable_open_and_read_text():
    m = build_model("reader_api")
    m.register()
    try:
        root = importlib.resources.files("runtime_models_reader_api")
        schema = find_schema_file(root)

        # read_text: default, with encoding, and with errors (module-level
        # importlib.resources.read_text always passes errors=)
        text = schema.read_text()
        assert json.loads(text)
        assert schema.read_text(encoding="utf-8") == text
        assert schema.read_text(encoding="utf-8", errors="strict") == text

        # open: binary mode
        with schema.open("rb") as stream:
            assert json.loads(stream.read())

        # open: text mode, default and with TextIOWrapper kwargs
        with schema.open() as stream:
            assert stream.read() == text
        with schema.open(encoding="utf-8", errors="strict") as stream:
            assert stream.read() == text

        # traversable resources are read-only
        with pytest.raises(ValueError, match="read-only"):
            schema.open("w")
    finally:
        m.unregister()


def test_in_memory_traversable_honours_encoding_and_errors():
    from oarepo_model.register import InMemoryTraversable

    t = InMemoryTraversable("pkg/file.txt", {"pkg/file.txt": "caf\u00e9"})
    assert t.read_bytes() == "caf\u00e9".encode("utf-8")
    assert t.read_text() == "caf\u00e9"
    assert t.read_text(encoding="utf-8") == "caf\u00e9"

    # the encoding hint reaches the codec instead of being ignored
    with pytest.raises(UnicodeDecodeError):
        t.read_text(encoding="ascii")
    # ... and errors is honoured the way bytes.decode honours it
    assert t.read_text(encoding="ascii", errors="replace") == "caf\ufffd\ufffd"

    with t.open("rb") as stream:
        assert stream.read() == "caf\u00e9".encode("utf-8")
    with t.open(encoding="utf-8") as stream:
        assert stream.read() == "caf\u00e9"

    missing = InMemoryTraversable("pkg/nope.txt", {"pkg/other.txt": "x"})
    with pytest.raises(FileNotFoundError):
        missing.read_text()
    with pytest.raises(FileNotFoundError):
        missing.open("rb")


def test_module_level_importlib_resources_functions():
    m = build_model("module_level_api")
    m.register()
    try:
        pkg = "runtime_models_module_level_api"
        root = importlib.resources.files(pkg)
        schema = find_schema_file(root)
        rel_path = f"jsonschemas/{schema.name}"
        text = schema.read_text()

        # read_text/open_binary/open_text all route through the traversable;
        # all of these used to raise on the in-memory traversable
        assert json.loads(importlib.resources.read_text(pkg, rel_path))
        with importlib.resources.open_binary(pkg, rel_path) as stream:
            assert json.loads(stream.read())
        with importlib.resources.open_text(pkg, rel_path, encoding="utf-8") as stream:
            assert stream.read() == text

        # as_file copies the in-memory resource to a real file
        with importlib.resources.as_file(schema) as path:
            assert path.read_text(encoding="utf-8") == text
    finally:
        m.unregister()


def test_resource_reader_interface():
    m = build_model("reader_direct_api")
    m.register()
    try:
        pkg = "runtime_models_reader_direct_api"
        root = importlib.resources.files(pkg)
        schema = find_schema_file(root)
        rel_path = f"jsonschemas/{schema.name}"

        spec = find_spec(pkg)
        reader = spec.loader.get_resource_reader(pkg)

        # these all raised NotImplementedError before
        assert reader.is_resource(rel_path)
        assert not reader.is_resource("jsonschemas")
        assert set(reader.contents()) == {"jsonschemas", "mappings"}
        with reader.open_resource(rel_path) as stream:
            assert json.loads(stream.read())
        with pytest.raises(FileNotFoundError):
            reader.resource_path(rel_path)
    finally:
        m.unregister()


def test_iterdir_is_deterministic():
    m = build_model("iterdir_determinism")
    m.register()
    try:
        root = importlib.resources.files("runtime_models_iterdir_determinism")

        listing = [c.name for c in root.iterdir()]
        assert listing == sorted(listing)

        # nested directories are deterministic as well
        jsonschemas = next(c for c in root.iterdir() if c.name == "jsonschemas")
        nested = [c.name for c in jsonschemas.iterdir()]
        assert nested == sorted(nested)

        # repeated iteration yields the same order
        assert [c.name for c in root.iterdir()] == listing
    finally:
        m.unregister()
