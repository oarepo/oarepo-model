#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from oarepo_model.api import model
from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations.high_level.set_synthetic_metadata import (
    SetSyntheticMetadata,
)
from oarepo_model.presets.records_resources import records_preset
from oarepo_model.presets.records_resources.records.synthetic_metadata import (
    MetadataField,
    MetadataProxy,
)

# ---------------------------------------------------------------------------
# SetSyntheticMetadata customization
# ---------------------------------------------------------------------------


def test_set_synthetic_metadata_writes_keys_into_dictionary():
    m = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(m, type_registry)
    builder.add_dictionary("synthetic_metadata")

    fn_a = lambda _: "value-a"  # noqa: E731
    fn_b = lambda d: d.get("title", "untitled")  # noqa: E731

    SetSyntheticMetadata(a=fn_a, b=fn_b).apply(builder, m)

    d = builder.get_dictionary("synthetic_metadata")
    assert d["a"] is fn_a
    assert d["b"] is fn_b


def test_set_synthetic_metadata_overrides_existing_keys():
    m = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(m, type_registry)
    builder.add_dictionary("synthetic_metadata", default={"a": "old"})

    fn_a = lambda _: "new"  # noqa: E731
    SetSyntheticMetadata(a=fn_a).apply(builder, m)

    assert builder.get_dictionary("synthetic_metadata")["a"] is fn_a


def test_set_synthetic_metadata_empty_kwargs_is_noop():
    m = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(m, type_registry)
    builder.add_dictionary("synthetic_metadata", default={"keep": "me"})

    SetSyntheticMetadata().apply(builder, m)

    assert dict(builder.get_dictionary("synthetic_metadata")) == {"keep": "me"}


# ---------------------------------------------------------------------------
# MetadataProxy
# ---------------------------------------------------------------------------


def test_metadata_proxy_returns_real_value_when_present():
    proxy = MetadataProxy({"a": 1}, {"a": lambda _: 99})
    # Real keys take precedence over synthetic ones.
    assert proxy["a"] == 1


def test_metadata_proxy_returns_synthetic_when_key_missing():
    proxy = MetadataProxy({}, {"computed": lambda _: 42})
    assert proxy["computed"] == 42


def test_metadata_proxy_synthetic_function_receives_wrapped_dict():
    wrapped = {"a": 1, "b": 2}
    proxy = MetadataProxy(wrapped, {"sum": lambda d: d["a"] + d["b"]})
    assert proxy["sum"] == 3


def test_metadata_proxy_no_synthetic_falls_through_to_wrapped():
    proxy = MetadataProxy({"x": "y"}, None)
    assert proxy["x"] == "y"
    with pytest.raises(KeyError):
        _ = proxy["missing"]


def test_metadata_proxy_unknown_key_with_synthetic_present_raises_keyerror():
    proxy = MetadataProxy({}, {"computed": lambda _: 42})
    with pytest.raises(KeyError):
        _ = proxy["other"]


def test_metadata_proxy_iteration_uses_wrapped_only():
    proxy = MetadataProxy({"a": 1}, {"b": lambda _: 2})
    # ObjectProxy delegates iteration / membership to the wrapped object;
    # synthetic keys are accessed through __getitem__ but not advertised.
    assert list(proxy) == ["a"]
    assert "a" in proxy
    assert "b" not in proxy


# ---------------------------------------------------------------------------
# MetadataField
# ---------------------------------------------------------------------------


class _RecordStub(dict):
    """Minimal record-like stub usable with invenio_records SystemField API."""


def test_metadata_field_wraps_dict_in_proxy_on_access():
    synthetic = {"title_lower": lambda d: d["title"].lower()}

    class Rec(_RecordStub):
        metadata = MetadataField(key="metadata", synthetic=synthetic)

    rec = Rec({"metadata": {"title": "Hello"}})
    md = rec.metadata
    assert isinstance(md, MetadataProxy)
    assert md["title"] == "Hello"
    assert md["title_lower"] == "hello"


def test_metadata_field_returns_proxy_when_key_absent():
    synthetic = {"static": lambda _: "S"}

    class Rec(_RecordStub):
        metadata = MetadataField(
            key="metadata",
            synthetic=synthetic,
            create_if_missing=False,
        )

    rec = Rec({})
    md = rec.metadata
    # Even with no underlying metadata dict, synthetic lookup still works.
    assert isinstance(md, MetadataProxy)
    assert md["static"] == "S"


# ---------------------------------------------------------------------------
# Preset wiring: building a model exposes synthetic_metadata + Record.metadata
# ---------------------------------------------------------------------------


_record_model_types = {
    "Metadata": {
        "properties": {
            "title": {"type": "fulltext+keyword"},
        }
    }
}


def test_records_preset_provides_synthetic_metadata_dictionary():
    m = model(
        name="synthetic_metadata_dict_test",
        version="1.0.0",
        presets=[records_preset],
        types=[_record_model_types],
        metadata_type="Metadata",
        customizations=[],
    )

    assert hasattr(m, "synthetic_metadata")
    assert m.synthetic_metadata == {}


def test_set_synthetic_metadata_in_built_model():
    m = model(
        name="synthetic_metadata_set_test",
        version="1.0.0",
        presets=[records_preset],
        types=[_record_model_types],
        metadata_type="Metadata",
        customizations=[
            SetSyntheticMetadata(
                title_upper=lambda d: d["title"].upper(),
            ),
        ],
    )

    assert "title_upper" in m.synthetic_metadata
    fn = m.synthetic_metadata["title_upper"]
    assert fn({"title": "abc"}) == "ABC"


def test_record_metadata_field_uses_synthetic_dictionary():
    m = model(
        name="synthetic_metadata_record_test",
        version="1.0.0",
        presets=[records_preset],
        types=[_record_model_types],
        metadata_type="Metadata",
        customizations=[
            SetSyntheticMetadata(
                title_upper=lambda d: d["title"].upper(),
            ),
        ],
    )

    # Build a record-like dict and access the descriptor directly so we don't
    # need a full SQLAlchemy / Flask stack.
    record_data = {"metadata": {"title": "hello"}}
    proxy = m.Record.metadata.__get__(record_data)
    assert isinstance(proxy, MetadataProxy)
    assert proxy["title"] == "hello"
    assert proxy["title_upper"] == "HELLO"
