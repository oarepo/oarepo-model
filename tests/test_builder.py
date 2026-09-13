# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

import itertools
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from oarepo_model.builder import (
    BuilderClass,
    BuilderClassList,
    BuilderConstant,
    BuilderDict,
    BuilderFile,
    BuilderList,
    BuilderModule,
    BuilderSymbolicLink,
    InvenioModelBuilder,
)
from oarepo_model.errors import (
    AlreadyRegisteredError,
    ClassBuildError,
    ClassListBuildError,
)


def test_builder_class():
    class A:
        pass

    class B(A):
        pass

    mock_model = MagicMock()
    mock_namespace = SimpleNamespace()

    b = BuilderClass("TestClass", base_classes=[A])
    assert repr(b) == "BuilderClass(key=TestClass)"
    b.add_mixins(B)
    clz = b.build(mock_model, mock_namespace)

    assert issubclass(clz, A)
    assert issubclass(clz, B)

    assert clz.mro() == [clz, B, A, object]

    with pytest.raises(RuntimeError):
        b.add_mixins(object)

    with pytest.raises(RuntimeError):
        b.add_base_classes(object)

    b = BuilderClass("TestClass", base_classes=[])
    b.add_mixins(A)
    b.add_base_classes(B)
    clz = b.build(mock_model, mock_namespace)
    assert clz.mro() == [clz, B, A, object]


def test_builder_class_inconsistent_mro():
    class A:
        pass

    class B:
        pass

    class C(A, B):
        pass

    class D(B, A):
        pass

    mock_model = MagicMock()
    mock_namespace = SimpleNamespace()

    b = BuilderClass("TestClass", base_classes=[C])
    b.add_mixins(D)

    with pytest.raises(ClassBuildError):
        b.build(mock_model, mock_namespace)


def test_builder_class_list():
    class A:
        pass

    class B(A):
        pass

    mock_model = MagicMock()
    mock_namespace = SimpleNamespace()

    b = BuilderClassList("TestClassList")
    assert repr(b) == "BuilderClassList(key=TestClassList)"
    b.extend([A])
    b.append(B)
    lst = b.build(mock_model, mock_namespace)

    assert lst == [B]

    with pytest.raises(RuntimeError):
        b.append(object)

    with pytest.raises(RuntimeError):
        b.extend([object])

    b = BuilderClassList("TestClassList")
    b.append(B)
    b.append(A)
    lst = b.build(mock_model, mock_namespace)
    assert lst == [B]


def test_builder_class_list_inconsistent_mro():
    class A:
        pass

    class B:
        pass

    class C(A, B):
        pass

    class D(B, A):
        pass

    mock_model = MagicMock()
    mock_namespace = SimpleNamespace()

    b = BuilderClassList("TestClassList")
    b.append(C)
    b.append(D)

    with pytest.raises(ClassListBuildError):
        b.build(mock_model, mock_namespace)


def test_builder_list():
    mock_model = MagicMock()
    mock_namespace = SimpleNamespace()

    b = BuilderList("TestList")
    assert repr(b) == "BuilderList(key=TestList)"

    b.extend([1])
    b.append(2)
    lst = b.build(mock_model, mock_namespace)

    assert lst == [1, 2]

    with pytest.raises(RuntimeError):
        b.append(object)

    with pytest.raises(RuntimeError):
        b.extend([object])


def test_builder_dict():
    mock_model = MagicMock()
    mock_namespace = SimpleNamespace()

    b = BuilderDict("TestDict")
    assert repr(b) == "BuilderDict(key=TestDict)"
    b["a"] = 1
    b["b"] = 2
    b["c"] = None
    b.update({"d": 3})
    dct = b.build(mock_model, mock_namespace)
    assert dct == {"a": 1, "b": 2, "d": 3}

    with pytest.raises(RuntimeError):
        b["d"] = 3

    with pytest.raises(RuntimeError):
        b.update({"e": 4})


def test_builder_constant():
    mock_model = MagicMock()
    mock_namespace = SimpleNamespace()

    b = BuilderConstant("CONST", 123)
    assert repr(b) == "BuilderConstant(key=CONST)"
    assert b.value == 123
    assert b.build(mock_model, mock_namespace) is None
    assert b.built


def test_builder_module_and_file():
    mock_model = MagicMock()
    mock_namespace = SimpleNamespace()

    mod = BuilderModule("mod1")
    assert repr(mod) == "BuilderModule(key=mod1)"
    mod.attr1 = 10
    mod.add_file("file1.txt", "content1")
    mod["_blah"] = 42
    built_mod = mod.build(mock_model, mock_namespace)
    assert hasattr(built_mod, "attr1")
    assert built_mod.attr1 == 10
    assert not hasattr(built_mod, "_blah")
    assert hasattr(built_mod, "__files__")
    assert built_mod.__files__["file1.txt"] == "content1"

    with pytest.raises(RuntimeError):
        mod["new_attr"] = 5

    file = BuilderFile("file1", "mod1", "file1.txt", "abc")
    result = file.build(mock_model, mock_namespace)
    assert result == {
        "module-name": "mod1",
        "file-path": "file1.txt",
        "content": "abc",
    }


def test_add_class_multiple_times():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    clz = builder.add_class("A")
    with pytest.raises(AlreadyRegisteredError):
        builder.add_class("A")
    clz1 = builder.add_class("A", exists_ok=True)
    assert clz is clz1


def test_add_class_list_multiple_times():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    clz = builder.add_class_list("AList")
    with pytest.raises(AlreadyRegisteredError):
        builder.add_class_list("AList")
    clz1 = builder.add_class_list("AList", exists_ok=True)
    assert clz is clz1


def test_add_list_multiple_times():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    lst = builder.add_list("AList")
    with pytest.raises(AlreadyRegisteredError):
        builder.add_list("AList")
    lst1 = builder.add_list("AList", exists_ok=True)
    assert lst is lst1


def test_add_dictionary_multiple_times():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    dct = builder.add_dictionary("ADict")
    with pytest.raises(AlreadyRegisteredError):
        builder.add_dictionary("ADict")
    dct1 = builder.add_dictionary("ADict", exists_ok=True)
    assert dct is dct1


def test_add_constant_multiple_times():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    const = builder.add_constant("AConst", 42)
    with pytest.raises(AlreadyRegisteredError):
        builder.add_constant("AConst", 42)
    const1 = builder.add_constant("AConst", 42, exists_ok=True)
    assert const is const1


def test_add_module_multiple_times():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    mod = builder.add_module("AModule")
    with pytest.raises(AlreadyRegisteredError):
        builder.add_module("AModule")
    mod1 = builder.add_module("AModule", exists_ok=True)
    assert mod is mod1


def test_add_file_multiple_times():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    builder.add_module("AModule")
    file = builder.add_file("AFile", "AModule", "blah.txt", "content")
    with pytest.raises(AlreadyRegisteredError):
        builder.add_file("AFile", "AModule", "blah.txt", "content")
    file1 = builder.add_file("AFile", "AModule", "blah.txt", "content", exists_ok=True)
    assert file is file1


ADDERS = {
    BuilderClass: lambda b, name, **kw: b.add_class(name, **kw),
    BuilderClassList: lambda b, name, **kw: b.add_class_list(name, **kw),
    BuilderList: lambda b, name, **kw: b.add_list(name, **kw),
    BuilderDict: lambda b, name, **kw: b.add_dictionary(name, **kw),
    BuilderConstant: lambda b, name, **kw: b.add_constant(name, 42, **kw),
    BuilderModule: lambda b, name, **kw: b.add_module(name, **kw),
    BuilderFile: lambda b, name, **kw: b.add_file(name, "AModule", "blah.txt", "content", **kw),
    BuilderSymbolicLink: lambda b, name, **kw: b.add_symlink(name, "AModule", "blah.txt", **kw),
}


@pytest.mark.parametrize("kind", list(ADDERS))
def test_add_existing_same_kind_returns_the_partial(kind):
    builder = InvenioModelBuilder(MagicMock(), MagicMock())
    partial = ADDERS[kind](builder, "A")
    assert ADDERS[kind](builder, "A", exists_ok=True) is partial
    with pytest.raises(AlreadyRegisteredError):
        ADDERS[kind](builder, "A")


@pytest.mark.parametrize(("first", "second"), list(itertools.permutations(ADDERS, 2)))
def test_add_existing_other_kind_raises(first, second):
    builder = InvenioModelBuilder(MagicMock(), MagicMock())
    ADDERS[first](builder, "A")
    with pytest.raises(TypeError, match=f"Partial A is not a {second.__name__}."):
        ADDERS[second](builder, "A", exists_ok=True)


def test_add_class_exists_ok_on_file_partial():
    builder = InvenioModelBuilder(MagicMock(), MagicMock())
    mapping = builder.add_file("record-mapping", "mappings", "record-v1.0.0.json", '{"mappings": {}}')

    with pytest.raises(TypeError, match="Partial record-mapping is not a BuilderClass"):
        builder.add_class("record-mapping", exists_ok=True)

    assert builder.get_file("record-mapping") is mapping
