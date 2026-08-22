#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Corner cases tests for utils."""

from __future__ import annotations

import copy

import pytest

from oarepo_model.utils import ReadOnlyDict, convert_to_python_identifier, dump_to_json


def test_read_only_dict():
    d = ReadOnlyDict({"a": 1, "b": 2})
    assert d["a"] == 1
    assert d["b"] == 2
    assert len(d) == 2
    assert list(d) == ["a", "b"]
    assert repr(d) == "ReadOnlyDict({'a': 1, 'b': 2})"
    dc = copy.deepcopy(d)
    assert dc["a"] == 1
    assert dc["b"] == 2
    assert len(dc) == 2
    assert list(dc) == ["a", "b"]
    assert repr(dc) == "ReadOnlyDict({'a': 1, 'b': 2})"
    assert d is not dc
    assert d._data is not dc._data  # noqa: SLF001


def test_convert_to_python_identifier():
    assert convert_to_python_identifier("") == "_empty_"
    assert convert_to_python_identifier("a") == "a"
    assert convert_to_python_identifier("a-b") == "a_45_b"
    assert convert_to_python_identifier("for") == "for_"


def test_dump_to_json():
    assert dump_to_json({"a": 1}) == '{"a": 1}'
    assert dump_to_json({"a": 1, "b": 2}) == '{"a": 1, "b": 2}'
    assert dump_to_json(ReadOnlyDict({"a": 1, "b": 2})) == '{"a": 1, "b": 2}'

    with pytest.raises(TypeError, match=r"Object of type .* is not JSON serializable"):
        assert dump_to_json(object())
