# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

import itertools
import warnings
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from werkzeug.local import LocalProxy

from oarepo_model.builder import (
    BuilderClass,
    BuilderClassList,
    BuilderDict,
    BuilderFile,
    BuilderList,
    BuilderModule,
    BuilderSymbolicLink,
    InvenioModelBuilder,
    Partial,
)
from oarepo_model.errors import (
    AlreadyRegisteredError,
    ClassBuildError,
    ClassListBuildError,
    ModelBuildError,
    PartialNotFoundError,
    PostBuildMutationWarning,
)
from oarepo_model.model import Dependency


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

    b = BuilderClass("TestClass", base_classes=[])
    b.add_mixins(A)
    b.add_base_classes(B)
    clz = b.build(mock_model, mock_namespace)
    assert clz.mro() == [clz, B, A, object]


def test_add_mixins_cannot_mutate_after_build():
    b = BuilderClass("TestClass", base_classes=[])
    b.build(MagicMock(), SimpleNamespace())

    with pytest.raises(RuntimeError):
        b.add_mixins("not-a-class")


def test_add_base_classes_cannot_mutate_after_build():
    b = BuilderClass("TestClass", base_classes=[])
    b.build(MagicMock(), SimpleNamespace())

    with pytest.raises(RuntimeError):
        b.add_base_classes("not-a-class")


def test_add_mixins_and_base_classes_do_not_validate_input_before_build():
    """add_mixins/add_base_classes only guard against post-build mutation, not argument type."""
    b = BuilderClass("TestClass", base_classes=[])
    b.add_mixins("not-a-class")
    b.add_base_classes(123)

    assert list(b.mixins) == ["not-a-class"]
    assert list(b.base_classes) == [123]


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

    with pytest.warns(PostBuildMutationWarning, match="items of partial 'TestClassList'"):
        b.append(A)

    with pytest.warns(PostBuildMutationWarning, match="items of partial 'TestClassList'"):
        b.extend([A])

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

    with pytest.warns(PostBuildMutationWarning, match="items of partial 'TestList'"):
        b.append(3)

    with pytest.warns(PostBuildMutationWarning, match="items of partial 'TestList'"):
        b.extend([4])


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

    with pytest.warns(PostBuildMutationWarning, match="items of partial 'TestDict'"):
        b["d"] = 3

    with pytest.warns(PostBuildMutationWarning, match="items of partial 'TestDict'"):
        b.update({"e": 4})


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


def test_builder_module_build_carries_callables_over_unchanged():
    """Only known descriptors are resolved; plain functions must not become bound methods."""
    mock_model = MagicMock()
    mock_namespace = SimpleNamespace(Record=object)

    def plain(value: object) -> object:
        return value

    def boom() -> str:
        raise AssertionError("LocalProxy was resolved at build time")

    mod = BuilderModule("mod1")
    mod.plain = plain
    mod.static = staticmethod(plain)
    mod.dep = Dependency("Record")
    mod.proxy = LocalProxy(boom)
    mod.add_file("file1.txt", "content1")

    built = mod.build(mock_model, mock_namespace)

    assert built.plain is plain
    assert built.static is plain
    assert built.dep is object
    assert isinstance(built.proxy, LocalProxy)
    assert built.__files__ == {"file1.txt": "content1"}


def test_builder_module_files_are_not_aliased():
    mock_model = MagicMock()
    mod = BuilderModule("mod1")
    mod.add_file("file1.txt", "content1")

    built = mod.build(mock_model, SimpleNamespace())

    mod.files["late.txt"] = "late"
    assert built.__files__ == {"file1.txt": "content1"}

    with pytest.raises(RuntimeError):
        mod.add_file("late.txt", "late")


def test_add_class_generated_name_keeps_acronyms():
    model = MagicMock()
    model.title_name = "Test"
    builder = InvenioModelBuilder(model, MagicMock())

    assert builder.add_class("ParentPIDProvider").class_name == "TestParentPIDProvider"
    assert builder.add_class("ParentProvider").class_name == "TestParentProvider"


@pytest.mark.parametrize(
    ("method", "args", "match"),
    [
        ("add_class", ("A",), None),
        ("add_class_list", ("AList",), None),
        ("add_list", ("AList",), None),
        ("add_dictionary", ("ADict",), None),
        ("add_module", ("AModule",), None),
        ("add_file", ("AFile", "AModule", "blah.txt", "content"), "File AFile already exists"),
        ("add_symlink", ("ALink", "AModule", "blah.txt"), "Symlink ALink already exists"),
    ],
    ids=["class", "class_list", "list", "dictionary", "module", "file", "symlink"],
)
def test_add_partial_multiple_times(method, args, match):
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    if method in ("add_file", "add_symlink"):
        builder.add_module("AModule")

    add = getattr(builder, method)
    partial = add(*args)
    with pytest.raises(AlreadyRegisteredError, match=match):
        add(*args)
    partial1 = add(*args, exists_ok=True)
    assert partial is partial1


def test_builder_symbolic_link_payload_shape():
    mock_model = MagicMock()
    mock_namespace = SimpleNamespace()

    link = BuilderSymbolicLink("link1", "mod1", "file1.txt")
    assert link.build(mock_model, mock_namespace) == {
        "module-name": "mod1",
        "file-path": "file1.txt",
        "content": None,
    }


def test_symlinks_are_not_collected_as_files():
    builder = InvenioModelBuilder(MagicMock(), MagicMock())
    builder.add_symlink("record-mapping-link", "mappings", "record.json")

    builder.collect_files()

    assert builder.ns.__files__ == {}
    assert builder.ns.__symlinks__ == {"record-mapping-link": "mappings/record.json"}


ADDERS = {
    BuilderClass: lambda b, name, **kw: b.add_class(name, **kw),
    BuilderClassList: lambda b, name, **kw: b.add_class_list(name, **kw),
    BuilderList: lambda b, name, **kw: b.add_list(name, **kw),
    BuilderDict: lambda b, name, **kw: b.add_dictionary(name, **kw),
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


def _all_partial_classes() -> list[type[Partial]]:
    classes: list[type[Partial]] = []
    stack = list(Partial.__subclasses__())
    while stack:
        clazz = stack.pop()
        classes.append(clazz)
        stack.extend(clazz.__subclasses__())
    return classes


@pytest.mark.parametrize("kind", _all_partial_classes(), ids=lambda clazz: clazz.__name__)
def test_get_missing_partial_raises_partial_not_found(kind):
    builder = InvenioModelBuilder(MagicMock(), MagicMock())
    with pytest.raises(PartialNotFoundError, match="missing not found"):
        builder._get("missing", kind)


def test_get_missing_partial_is_a_model_build_error():
    """PartialNotFoundError is a ModelBuildError, so callers can catch build failures generically."""
    builder = InvenioModelBuilder(MagicMock(), MagicMock())
    with pytest.raises(ModelBuildError, match="missing not found"):
        builder._get("missing", BuilderClass)


def test_get_file_missing_names_the_kind():
    builder = InvenioModelBuilder(MagicMock(), MagicMock())
    with pytest.raises(PartialNotFoundError, match="Builder file AFile not found"):
        builder.get_file("AFile")


def test_get_missing_partial_without_message_falls_back_to_class_name():
    class CustomPartial(Partial):
        pass

    builder = InvenioModelBuilder(MagicMock(), MagicMock())
    with pytest.raises(PartialNotFoundError, match="CustomPartial missing not found"):
        builder._get("missing", CustomPartial)


def _entry_point_builder() -> InvenioModelBuilder:
    return InvenioModelBuilder(MagicMock(in_memory_package_name="runtime_models_record"), MagicMock())


def test_builder_class_module_points_at_model_package():
    """Generated classes are importable from the model's in-memory package, not the builder."""
    mock_model = MagicMock(in_memory_package_name="runtime_models_test")

    clz = BuilderClass("TestClass").build(mock_model, SimpleNamespace())

    assert clz.__module__ == "runtime_models_test"
    assert clz.__qualname__ == "TestClass"
    assert repr(clz) == "<class 'runtime_models_test.TestClass'>"


def test_add_entry_point():
    builder = _entry_point_builder()
    builder.add_entry_point("invenio_base.api_blueprints", "records", "records_blueprint")
    builder.add_entry_point("invenio_cms.modules", "widgets", "widgets", separator=".")

    assert builder.entry_points == {
        ("invenio_base.api_blueprints", "records"): "runtime_models_record:records_blueprint",
        ("invenio_cms.modules", "widgets"): "runtime_models_record.widgets",
    }


def test_add_entry_point_twice_raises():
    builder = _entry_point_builder()
    builder.add_entry_point("g", "n", "v")

    with pytest.raises(AlreadyRegisteredError):
        builder.add_entry_point("g", "n", "other")

    assert builder.entry_points == {("g", "n"): "runtime_models_record:v"}


def test_add_entry_point_overwrite():
    builder = _entry_point_builder()
    builder.add_entry_point("g", "n", "v")
    builder.add_entry_point("g", "n", "other", overwrite=True)

    assert builder.entry_points == {("g", "n"): "runtime_models_record:other"}


def test_removing_entry_point_with_none_value():
    builder = _entry_point_builder()
    builder.add_entry_point("g", "n", "v")
    builder.add_entry_point("g", "n", None)

    assert builder.entry_points == {}


def test_removing_absent_entry_point_with_none_value_registers_nothing():
    builder = _entry_point_builder()
    builder.add_entry_point("g", "n", None)

    assert builder.entry_points == {}


def test_removed_entry_point_is_not_built():
    builder = _entry_point_builder()
    builder.add_entry_point("invenio_base.api_blueprints", "records", "records_blueprint")
    builder.add_entry_point("invenio_base.api_blueprints", "records", None)

    assert builder.build().entry_points == []


def test_builder_class_add_field():
    mock_model = MagicMock()
    mock_namespace = SimpleNamespace()

    b = BuilderClass("TestClass", base_classes=[])
    b.add_field("table", "record")
    clz = b.build(mock_model, mock_namespace)

    assert vars(clz)["table"] == "record"

    with pytest.raises(RuntimeError):
        b.add_field("other", "x")


def test_builder_class_set_mixins_and_base_classes():
    class A:
        pass

    class B:
        pass

    mock_model = MagicMock()
    mock_namespace = SimpleNamespace()

    b = BuilderClass("TestClass", base_classes=[A])
    b.add_base_classes(B)
    b.set_base_classes(A)
    b.set_mixins(B)
    clz = b.build(mock_model, mock_namespace)

    assert clz.mro() == [clz, B, A, object]

    with pytest.raises(RuntimeError):
        b.set_base_classes()

    with pytest.raises(RuntimeError):
        b.set_mixins()


def test_builder_class_field_mutation_before_build_is_silent():
    """The raw containers still work before the partial is built, without warnings."""

    class A:
        pass

    class B(A):
        pass

    mock_model = MagicMock()
    mock_namespace = SimpleNamespace()

    b = BuilderClass("TestClass", base_classes=[A])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        b.base_classes.append(B)
        b.fields["table"] = "record"
        b.mixins = []

    clz = b.build(mock_model, mock_namespace)

    assert issubclass(clz, B)
    assert vars(clz)["table"] == "record"


def test_builder_class_mutation_after_build_warns():
    """Raw container mutations used to be silently lost, which hid missing `modifies`."""
    mock_model = MagicMock()
    mock_namespace = SimpleNamespace()

    b = BuilderClass("TestClass", base_classes=[])
    b.build(mock_model, mock_namespace)

    with pytest.warns(PostBuildMutationWarning, match="base_classes of partial 'TestClass'"):
        b.base_classes.append(object)

    with pytest.warns(PostBuildMutationWarning, match="fields of partial 'TestClass'"):
        b.fields["table"] = "record"

    with pytest.warns(PostBuildMutationWarning, match="mixins of partial 'TestClass'"):
        b.mixins = []

    with pytest.warns(PostBuildMutationWarning):
        b.fields.update({"other": "x"})
