# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Invenio model builder for constructing and managing model components.

This module provides the InvenioModelBuilder class that handles the construction
and management of Invenio model components. It manages class registration,
dependency resolution, and dynamic component creation for OARepo models.
"""

from __future__ import annotations

import warnings
from collections import defaultdict
from importlib.metadata import EntryPoint
from types import MappingProxyType, SimpleNamespace
from typing import TYPE_CHECKING, Any, override

from werkzeug.local import LocalProxy

from oarepo_model.errors import (
    AlreadyRegisteredError,
    ClassBuildError,
    ClassListBuildError,
    PartialNotFoundError,
    PostBuildMutationWarning,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, SupportsIndex

    from .datatypes.registry import DataTypeRegistry
    from .presets.base import Preset

from .model import CachedDescriptor, FileContent, InvenioModel, RuntimeDependencies
from .utils import (
    is_mro_consistent,
    make_mro_consistent,
    title_case,
)


class Partial:
    """Base class for partial customizations in the model."""

    def __init__(self, key: str):
        """Initialize the Partial customization."""
        self.key = key
        self.built = False

    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> Any:
        """Build the class from the partial."""
        raise NotImplementedError("Subclasses must implement this method.")  # pragma: no cover

    @override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(key={self.key})"


def _warn_post_build_mutation(owner: Partial, attribute: str, stacklevel: int) -> None:
    """Warn that a mutation performed after the partial was built is silently lost."""
    if owner.built:
        warnings.warn(
            f"{attribute} of partial '{owner.key}' was modified after the partial was built, so the "
            f"change has no effect on what is generated. Make the preset performing the modification "
            f"declare '{owner.key}' in its modifies and use the guarded BuilderClass methods instead "
            f"of the containers directly; this will raise RuntimeError in a future version.",
            PostBuildMutationWarning,
            stacklevel=stacklevel,
        )


class _GuardedList[T](list[T]):
    """List of a partial that warns when it is modified after the partial was built."""

    def __init__(self, owner: Partial, attribute: str, values: Iterable[T] = ()) -> None:
        """Initialize the guarded list."""
        super().__init__(values)
        self._owner = owner
        self._attribute = attribute

    def _guard(self) -> None:
        _warn_post_build_mutation(self._owner, self._attribute, stacklevel=4)

    @override
    def append(self, object: T) -> None:
        self._guard()
        super().append(object)

    @override
    def extend(self, iterable: Iterable[T]) -> None:
        self._guard()
        super().extend(iterable)

    @override
    def insert(self, index: SupportsIndex, object: T) -> None:
        self._guard()
        super().insert(index, object)

    @override
    def __setitem__(self, index: Any, value: Any) -> None:
        self._guard()
        super().__setitem__(index, value)

    @override
    def pop(self, index: SupportsIndex = -1) -> T:
        self._guard()
        return super().pop(index)

    @override
    def clear(self) -> None:
        self._guard()
        super().clear()


class _GuardedDict(dict[str, Any]):
    """Dictionary of a partial that warns when it is modified after the partial was built."""

    def __init__(self, owner: Partial, attribute: str, values: dict[str, Any] | None = None) -> None:
        """Initialize the guarded dictionary."""
        super().__init__(values or {})
        self._owner = owner
        self._attribute = attribute

    def _guard(self) -> None:
        _warn_post_build_mutation(self._owner, self._attribute, stacklevel=4)

    @override
    def __setitem__(self, key: str, value: Any) -> None:
        self._guard()
        super().__setitem__(key, value)

    @override
    def update(self, *args: Any, **kwargs: Any) -> None:
        self._guard()
        super().update(*args, **kwargs)

    @override
    def setdefault(self, key: str, default: Any = None) -> Any:
        self._guard()
        return super().setdefault(key, default)

    @override
    def pop(self, *args: Any) -> Any:
        self._guard()
        return super().pop(*args)

    @override
    def clear(self) -> None:
        self._guard()
        super().clear()


class BuilderClass(Partial):
    """Builder for classes in the model."""

    def __init__(
        self,
        class_name: str,
        mixins: list[type] | None = None,
        base_classes: list[type] | None = None,
        fields: dict[str, Any] | None = None,
    ):
        """Initialize the BuilderClass customization."""
        super().__init__(key=class_name)
        self.class_name = class_name
        self._mixins = _GuardedList(self, "mixins", mixins or ())
        self._base_classes = _GuardedList(self, "base_classes", base_classes or ())
        self._fields = _GuardedDict(self, "fields", fields)

    @property
    def mixins(self) -> _GuardedList[type]:
        """Mixins of the class; prefer add_mixins / set_mixins over assigning to it."""
        return self._mixins

    @mixins.setter
    def mixins(self, value: Iterable[type]) -> None:
        _warn_post_build_mutation(self, "mixins", stacklevel=3)
        self._mixins = _GuardedList(self, "mixins", value)

    @property
    def base_classes(self) -> _GuardedList[type]:
        """Base classes of the class; prefer add_base_classes / set_base_classes over assigning."""
        return self._base_classes

    @base_classes.setter
    def base_classes(self, value: Iterable[type]) -> None:
        _warn_post_build_mutation(self, "base_classes", stacklevel=3)
        self._base_classes = _GuardedList(self, "base_classes", value)

    @property
    def fields(self) -> _GuardedDict:
        """Fields of the class; prefer add_field over assigning to it."""
        return self._fields

    @fields.setter
    def fields(self, value: dict[str, Any]) -> None:
        _warn_post_build_mutation(self, "fields", stacklevel=3)
        self._fields = _GuardedDict(self, "fields", value)

    def add_base_classes(self, *classes: type) -> None:
        """Add base classes to the class."""
        if self.built:
            raise RuntimeError("Cannot add base classes after the class is built.")
        self._base_classes.extend(classes)

    def set_base_classes(self, *classes: type) -> None:
        """Replace the base classes of the class."""
        if self.built:
            raise RuntimeError("Cannot set base classes after the class is built.")
        self._base_classes = _GuardedList(self, "base_classes", classes)

    def add_mixins(self, *classes: type) -> None:
        """Add mixins to the class."""
        if self.built:
            raise RuntimeError("Cannot add mixins after the class is built.")
        for clazz in reversed(classes):
            self._mixins.insert(0, clazz)  # Prepend to preserve MRO

    def set_mixins(self, *classes: type) -> None:
        """Replace the mixins of the class."""
        if self.built:
            raise RuntimeError("Cannot set mixins after the class is built.")
        self._mixins = _GuardedList(self, "mixins", classes)

    def add_field(self, name: str, value: Any) -> None:
        """Add a field to the class."""
        if self.built:
            raise RuntimeError("Cannot add fields after the class is built.")
        self._fields[name] = value

    @override
    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> type:
        self.built = True
        base_list: list[type] = [
            *self.mixins,
            *self.base_classes,
        ]
        try:
            if not is_mro_consistent(base_list):
                # If the MRO is not consistent, we need to make it consistent
                base_list = make_mro_consistent(base_list)
        except Exception as e:
            raise ClassBuildError(
                f"Error while building class {self.class_name}: {base_list} {e}",
            ) from e

        return type(
            self.class_name,
            tuple(base_list),
            {
                # __module__ deliberately points at the model's in-memory package (not this
                # builder module), so tracebacks, repr and dotted-path resolution (pickle,
                # marshmallow Nested) resolve to runtime_models_<base_name>.<Class> instead
                # of oarepo_model.builder.<Class> - see InvenioModel.in_memory_package_name.
                "__module__": model.in_memory_package_name,
                "__qualname__": self.class_name,
                "oarepo_model": model,
                "oarepo_model_namespace": namespace,
                **self.fields,
            },
        )


class BuilderClassList(Partial, _GuardedList[type]):
    """Builder for class lists in the model."""

    def __init__(self, key: str, values: Iterable[type] = ()) -> None:
        """Initialize the class list partial."""
        Partial.__init__(self, key)
        _GuardedList.__init__(self, self, "items", values)

    @override
    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> list[type]:
        """Build a class list from the partial."""
        self.built = True
        try:
            return make_mro_consistent(self)
        except Exception as e:
            raise ClassListBuildError(
                f"Error while building class list {self}: {e}",
            ) from e


class BuilderList(Partial, _GuardedList[Any]):
    """Builder for lists in the model."""

    def __init__(self, key: str, values: Iterable[Any] = ()) -> None:
        """Initialize the list partial."""
        Partial.__init__(self, key)
        _GuardedList.__init__(self, self, "items", values)

    @override
    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> list[Any]:
        """Build a list from the partial."""
        self.built = True
        return list(self)


class BuilderDict(Partial, _GuardedDict):
    """Builder for dictionaries in the model."""

    def __init__(self, key: str, values: dict[str, Any] | None = None) -> None:
        """Initialize the dictionary partial."""
        Partial.__init__(self, key)
        _GuardedDict.__init__(self, self, "items", values)

    @override
    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> dict[str, Any]:
        """Build a dictionary from the partial."""
        self.built = True
        return {k: v for k, v in self.items() if v is not None}


class BuilderConstant(Partial):
    """Builder for constants in the model."""

    def __init__(self, key: str, value: Any):
        """Initialize the BuilderConstant customization."""
        super().__init__(key)
        self.value = value

    @override
    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> None:
        """Build a dictionary from the partial."""
        self.built = True


class BuilderModule(Partial, SimpleNamespace):
    """Builder for modules in the model."""

    def __init__(self, module_name: str):
        """Initialize the BuilderModule customization."""
        super().__init__(module_name)
        self.files: dict[str, FileContent] = {}

    @override
    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> Any:
        """Build a module from the partial."""
        self.built = True
        ret = SimpleNamespace()
        ret.__files__ = dict(self.files)
        for attr in self.__dict__:
            try:
                if attr.startswith("_") and attr != "__file__":
                    continue
                value = getattr(self, attr)
                if isinstance(value, LocalProxy):
                    # must stay lazy, resolving it here would require an app context
                    pass
                elif isinstance(value, (staticmethod, classmethod)):
                    value = value.__get__(None, type(self))
                elif isinstance(value, CachedDescriptor):
                    value = value.real_get_value(None, type(self), model, namespace)
                setattr(ret, attr, value)
            except Exception as e:
                raise RuntimeError(
                    f"Error while building module {self.key} attribute {attr}: {e}",
                ) from e
        return ret

    def add_file(self, file_path: str, content: FileContent) -> None:
        """Add a file to the module."""
        if self.built:
            raise RuntimeError("Cannot add files after the module is built.")
        self.files[file_path] = content

    def __setitem__(self, key: str, value: Any) -> None:
        """Simulate a dictionary's x["key"] = value."""
        if self.built:
            raise RuntimeError("Cannot set item after the module is built.")
        setattr(self, key, value)


class _FileLike(Partial):
    """Shared base of file and symlink partials: one payload shape for both."""

    def __init__(
        self,
        name: str,
        module_name: str,
        file_path: str,
        content: FileContent | None,
    ) -> None:
        """Initialize the file-like partial."""
        super().__init__(name)
        self.module_name = module_name
        self.file_path = file_path
        self.content = content

    @override
    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> dict[str, Any]:
        """Build the payload describing where the file lives."""
        self.built = True

        return {
            "module-name": self.module_name,
            "file-path": self.file_path,
            "content": self.content,
        }


class BuilderFile(_FileLike):
    """Builder for files in the model."""

    content: FileContent


class BuilderSymbolicLink(_FileLike):
    """Builder for symbolic links in the model; its content is the link target's."""

    content: None

    def __init__(self, name: str, module_name: str, file_path: str) -> None:
        """Initialize the symlink partial."""
        super().__init__(name, module_name, file_path, None)


class InvenioModelBuilder:
    """Builder for Invenio models."""

    def __init__(self, model: InvenioModel, type_registry: DataTypeRegistry):
        """Initialize the InvenioModelBuilder."""
        self.model = model
        self.ns = SimpleNamespace()
        self.partials: dict[str, Partial] = {}
        self.entry_points: dict[tuple[str, str], str] = {}
        self.runtime_dependencies = RuntimeDependencies()
        self.type_registry = type_registry
        self.current_preset: Preset | None = None
        #: which preset created which partial, and which presets touched which partial
        self.created_by: dict[str, Preset] = {}
        self.touched_by: dict[str, set[Preset]] = defaultdict(set)

    def start_preset(self, preset: Preset) -> None:
        """Attribute the partials created and used from now on to `preset`."""
        self.current_preset = preset

    def finish_preset(self) -> None:
        """Stop attributing partials to the preset being applied."""
        self.current_preset = None

    def _record(self, name: str, *, created: bool) -> None:
        """Remember what the preset being applied does with partials."""
        preset = self.current_preset
        if preset is None:
            return
        if created:
            self.created_by[name] = preset
        else:
            self.touched_by[name].add(preset)

    def _add[T: Partial](
        self,
        name: str,
        clz: type[T],
        exists_ok: bool,
        label: str,
        create: Callable[[], T],
    ) -> T:
        """Add a partial, checking its kind with `_get` when `exists_ok` is set."""
        if name in self.partials:
            if exists_ok:
                return self._get(name, clz)
            raise AlreadyRegisteredError(f"{label} {name} already exists.")
        self.partials[name] = ret = create()
        self._record(name, created=True)
        return ret

    def add_class(
        self,
        name: str,
        clazz: type | None = None,
        exists_ok: bool = False,
    ) -> BuilderClass:
        """Add a class to the builder."""
        return self._add(
            name,
            BuilderClass,
            exists_ok,
            "Class",
            lambda: BuilderClass(
                self.model.title_name + title_case(name),
                base_classes=[clazz] if clazz else [],
            ),
        )

    def get_class(self, name: str) -> BuilderClass:
        """Get a class by name."""
        return self._get(name, BuilderClass)

    def add_class_list(
        self,
        name: str,
        *classes: type,
        exists_ok: bool = False,
    ) -> BuilderClassList:
        """Add a class list to the builder.

        A class list is a list of classes that will be used to build a mro consistent class list.
        """

        def create() -> BuilderClassList:
            cll = BuilderClassList(name)
            cll.extend(classes)
            return cll

        return self._add(name, BuilderClassList, exists_ok, "Class list", create)

    def get_class_list(self, name: str) -> BuilderClassList:
        """Get a class list by name."""
        return self._get(name, BuilderClassList)

    def add_list(
        self,
        name: str,
        *classes: type,
        exists_ok: bool = False,
    ) -> BuilderList:
        """Add a list to the builder."""

        def create() -> BuilderList:
            lst = BuilderList(name)
            lst.extend(classes)
            return lst

        return self._add(name, BuilderList, exists_ok, "List", create)

    def get_list(self, name: str) -> BuilderList:
        """Get a list by name."""
        return self._get(name, BuilderList)

    def add_dictionary(
        self,
        name: str,
        default: dict[str, Any] | None = None,
        exists_ok: bool = False,
    ) -> BuilderDict:
        """Add a dictionary to the builder."""

        def create() -> BuilderDict:
            ret = BuilderDict(name)
            ret.update(default or {})
            return ret

        return self._add(name, BuilderDict, exists_ok, "Dictionary", create)

    def get_dictionary(self, name: str) -> dict[str, Any]:
        """Get a dictionary by name."""
        return self._get(name, BuilderDict)

    def add_constant(
        self,
        name: str,
        value: Any,
        exists_ok: bool = False,
    ) -> BuilderConstant:
        """Add a constant to the builder."""
        return self._add(name, BuilderConstant, exists_ok, "Constant", lambda: BuilderConstant(name, value))

    def get_constant(self, name: str) -> BuilderConstant:
        """Get a constant by name."""
        return self._get(name, BuilderConstant)

    def add_module(
        self,
        name: str,
        exists_ok: bool = False,
    ) -> BuilderModule:
        """Add a module to the builder."""
        return self._add(name, BuilderModule, exists_ok, "Module", lambda: BuilderModule(name))

    def add_file(
        self,
        symbolic_name: str,
        module_name: str,
        file_path: str,
        content: FileContent,
        exists_ok: bool = False,
    ) -> BuilderFile:
        """Add a file to the builder."""
        return self._add(
            symbolic_name,
            BuilderFile,
            exists_ok,
            "File",
            lambda: BuilderFile(symbolic_name, module_name, file_path, content),
        )

    def add_symlink(
        self,
        symbolic_name: str,
        module_name: str,
        file_path: str,
        exists_ok: bool = False,
    ) -> BuilderSymbolicLink:
        """Add a symlink to the builder."""
        return self._add(
            symbolic_name,
            BuilderSymbolicLink,
            exists_ok,
            "Symlink",
            lambda: BuilderSymbolicLink(symbolic_name, module_name, file_path),
        )

    def get_file(self, symbolic_name: str) -> BuilderFile:
        """Get a file by symbolic name."""
        return self._get(symbolic_name, BuilderFile)

    def get_module(self, name: str) -> BuilderModule:
        """Get a module by name."""
        return self._get(name, BuilderModule)

    def add_entry_point(
        self,
        group: str,
        name: str,
        value: str | None,
        overwrite: bool = False,
        separator: str = ":",
    ) -> None:
        """Add an entry point to the builder, or remove it when `value` is None."""
        if value is None:
            self.entry_points.pop((group, name), None)
            return

        if (group, name) in self.entry_points and not overwrite:
            raise AlreadyRegisteredError(f"Entry point {group}:{name} already exists.")

        self.entry_points[(group, name)] = f"{self.model.in_memory_package_name}{separator}{value}"

    _not_found_messages = MappingProxyType[type, str](
        {
            BuilderClass: "Builder class",
            BuilderClassList: "Builder class list",
            BuilderList: "Builder list",
            BuilderDict: "Builder dictionary",
            BuilderModule: "Builder module",
            BuilderConstant: "Builder constant",
            BuilderFile: "Builder file",
            BuilderSymbolicLink: "Builder symbolic link",
        },
    )

    def _get[T](self, name: str, clz: type[T]) -> T:
        """Get a partial by name."""
        if name not in self.partials:
            raise PartialNotFoundError(
                f"{self._not_found_messages.get(clz, clz.__name__)} {name} not found.",
            )
        partial = self.partials[name]
        if not isinstance(partial, clz):
            raise TypeError(f"Partial {name} is not a {clz.__name__}.")
        self._record(name, created=False)
        return partial

    def get_runtime_dependencies(self) -> RuntimeDependencies:
        """Get the runtime dependencies of the model."""
        return self.runtime_dependencies

    def build_partial(self, key: str) -> Any:
        """Build a partial by key."""
        if not hasattr(self.ns, key):
            if key not in self.partials:
                raise PartialNotFoundError(f"Partial {key} not found.")
            partial = self.partials[key]
            ret = partial.build(self.model, self.ns)
            setattr(self.ns, key, ret)
            return ret
        return getattr(self.ns, key)

    def collect_files(self) -> None:
        """Collect all files from the partials into the namespace."""
        self.ns.__files__ = {}
        self.ns.__symlinks__ = {}

        for partial in self.partials.values():
            if not isinstance(partial, BuilderFile):
                continue

            self.ns.__files__[f"{partial.module_name}/{partial.file_path}"] = partial.content

        for partial in self.partials.values():
            if not isinstance(partial, BuilderSymbolicLink):
                continue

            self.ns.__symlinks__[partial.key] = f"{partial.module_name}/{partial.file_path}"

    def build(self) -> SimpleNamespace:
        """Build the model from the collected partials."""
        for key in self.partials:
            self.build_partial(key)

        # TODO: need to have entry points separate from the partials ???
        entry_points = []
        for group, name in self.entry_points:
            value = self.entry_points[(group, name)]
            entry_points.append(EntryPoint(group=group, name=name, value=value))

        self.ns.entry_points = entry_points
        self.runtime_dependencies.bind_dependencies(self.ns)
        self.collect_files()
        return self.ns
