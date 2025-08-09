#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Invenio model builder for constructing and managing model components.

This module provides the InvenioModelBuilder class that handles the construction
and management of Invenio model components. It manages class registration,
dependency resolution, and dynamic component creation for OARepo models.
"""

from __future__ import annotations

from importlib.metadata import EntryPoint
from types import MappingProxyType, SimpleNamespace
from typing import TYPE_CHECKING, Any, cast, override

from werkzeug.local import LocalProxy

from oarepo_model.errors import (
    AlreadyRegisteredError,
    ClassBuildError,
    PartialNotFoundError,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .datatypes.registry import DataTypeRegistry

from .model import InvenioModel, RuntimeDependencies
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
        raise NotImplementedError("Subclasses must implement this method.")

    @override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(key={self.key})"


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
        self.mixins = list(mixins) if mixins else []
        self.base_classes = list(base_classes) if base_classes else []
        self.fields = fields if fields else {}

    def add_base_classes(self, *classes: type) -> None:
        """Add base classes to the class."""
        if self.built:
            raise RuntimeError("Cannot add base classes after the class is built.")
        self.base_classes.extend(classes)

    def add_mixins(self, *classes: type) -> None:
        """Add mixins to the class."""
        if self.built:
            raise RuntimeError("Cannot add mixins after the class is built.")
        for clazz in reversed(classes):
            self.mixins.insert(0, clazz)  # Prepend to preserve MRO

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
                "__module__": type(self).__module__,
                "__qualname__": self.class_name,
                "oarepo_model": model,
                "oarepo_model_namespace": namespace,
                **self.fields,
            },
        )


class BuilderClassList(Partial, list[type]):
    """Builder for class lists in the model."""

    @override
    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> list[type]:
        """Build a class list from the partial."""
        self.built = True
        if not is_mro_consistent(self):
            # If the MRO is not consistent, we need to make it consistent
            return make_mro_consistent(self)
        return list(self)

    @override
    def append(self, object: type) -> None:
        if self.built:
            raise RuntimeError("Cannot append to class list after it is built.")
        return super().append(object)

    @override
    def extend(self, iterable: Iterable[type]) -> None:
        if self.built:
            raise RuntimeError("Cannot append to class list after it is built.")
        return super().extend(iterable)


class BuilderList(Partial, list[Any]):
    """Builder for lists in the model."""

    @override
    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> list[Any]:
        self.built = True
        return list(self)

    @override
    def append(self, object: type) -> None:
        if self.built:
            raise RuntimeError("Cannot append to class list after it is built.")
        return super().append(object)

    @override
    def extend(self, iterable: Iterable[type]) -> None:
        if self.built:
            raise RuntimeError("Cannot append to class list after it is built.")
        return super().extend(iterable)


class BuilderDict(Partial, dict[str, Any]):
    """Builder for dictionaries in the model."""

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
        self.files: dict[str, str] = {}

    @override
    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> Any:
        """Build a module from the partial."""
        self.built = True
        # iterate through all attributes of the simple namespace and
        # if any of those has a __get__ method, call it. This will handle
        # Dependency descriptors and other similar cases.
        ret = SimpleNamespace()
        ret.__files__ = self.files
        for attr in self.__dict__:
            try:
                if attr.startswith("_") and attr != "__file__":
                    continue
                value = getattr(self, attr)
                if callable(value) and not isinstance(value, LocalProxy) and hasattr(value, "__get__"):
                    value = value.__get__(self, type(self))
                setattr(ret, attr, value)
            except Exception as e:
                raise RuntimeError(
                    f"Error while building module {self.key} attribute {attr}: {e}",
                ) from e
        return ret

    def add_file(self, file_path: str, content: str) -> None:
        """Add a file to the module."""
        self.files[file_path] = content

    def __setitem__(self, key: str, value: Any) -> None:
        """Simulate a dictionary's x["key"] = value."""
        if self.built:
            raise RuntimeError("Cannot set item after the module is built.")
        setattr(self, key, value)


class BuilderFile(Partial):
    """Builder for files in the model."""

    def __init__(self, name: str, module_name: str, file_path: str, content: str):
        """Initialize the BuilderFile customization."""
        super().__init__(name)
        self.module_name = module_name
        self.file_path = file_path
        self.content = content

    @override
    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> Any:
        self.built = True

        return {
            "module-name": self.module_name,
            "file-path": self.file_path,
            "content": self.content,
        }


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

    def add_class(
        self,
        name: str,
        clazz: type | None = None,
        exists_ok: bool = False,  # noqa: FBT002 - boolean argument to keep a single method
    ) -> BuilderClass:
        """Add a class to the builder."""
        if name in self.partials:
            if exists_ok:
                return cast("BuilderClass", self.partials[name])
            raise AlreadyRegisteredError(f"Class {name} already exists.")
        self.partials[name] = clz = BuilderClass(
            self.model.title_name + title_case(name).replace("_", ""),
            base_classes=[clazz] if clazz else [],
        )
        return clz

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
        if name in self.partials:
            if exists_ok:
                return cast("BuilderClassList", self.partials[name])
            raise AlreadyRegisteredError(f"Class list {name} already exists.")
        self.partials[name] = cll = BuilderClassList(name)
        cll.extend(classes)
        return cll

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
        if name in self.partials:
            if exists_ok:
                return cast("BuilderList", self.partials[name])
            raise AlreadyRegisteredError(f"List {name} already exists.")
        self.partials[name] = cll = BuilderList(name)
        cll.extend(classes)
        return cll

    def get_list(self, name: str) -> BuilderList:
        """Get a list by name."""
        return self._get(name, BuilderList)

    def add_dictionary(
        self,
        name: str,
        default: dict[str, Any] | None = None,
        exists_ok: bool = False,  # noqa: FBT002 - boolean argument to keep a single method
    ) -> BuilderDict:
        """Add a dictionary to the builder."""
        if name in self.partials:
            if exists_ok:
                return cast("BuilderDict", self.partials[name])
            raise AlreadyRegisteredError(f"Dictionary {name} already exists.")
        self.partials[name] = ret = BuilderDict(name)
        ret.update(default or {})
        return ret

    def get_dictionary(self, name: str) -> dict[str, Any]:
        """Get a dictionary by name."""
        return self._get(name, BuilderDict)

    def add_constant(
        self,
        name: str,
        value: Any,
        exists_ok: bool = False,  # noqa: FBT002 - boolean argument to keep a single method
    ) -> BuilderConstant:
        """Add a constant to the builder."""
        if name in self.partials:
            if exists_ok:
                return cast("BuilderConstant", self.partials[name])
            raise AlreadyRegisteredError(f"Constant {name} already exists.")
        self.partials[name] = ret = BuilderConstant(name, value)
        return ret

    def get_constant(self, name: str) -> BuilderConstant:
        """Get a constant by name."""
        return self._get(name, BuilderConstant)

    def add_module(
        self,
        name: str,
        exists_ok: bool = False,  # noqa: FBT002 - boolean argument to keep a single method
    ) -> BuilderModule:
        """Add a module to the builder."""
        if name in self.partials:
            if exists_ok:
                return cast("BuilderModule", self.partials[name])
            raise AlreadyRegisteredError(f"Module {name} already exists.")
        self.partials[name] = _module = BuilderModule(name)
        return _module

    def add_file(
        self,
        symbolic_name: str,
        module_name: str,
        file_path: str,
        content: str,
        exists_ok: bool = False,  # noqa: FBT002 - boolean argument to keep a single method
    ) -> BuilderFile:
        """Add a file to the builder."""
        if symbolic_name in self.partials:
            if exists_ok:
                return cast("BuilderFile", self.partials[symbolic_name])
            raise AlreadyRegisteredError(f"Module {symbolic_name} already exists.")

        ret = BuilderFile(symbolic_name, module_name, file_path, content)
        self.partials[symbolic_name] = ret
        return ret

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
        overwrite: bool = False,  # noqa: FBT002 - boolean argument to keep a single method
        separator: str = ":",
    ) -> None:
        """Add an entry point to the builder."""
        if (group, name) in self.entry_points and not overwrite:
            raise AlreadyRegisteredError(f"Entry point {group}:{name} already exists.")

        if value is None and (group, name) in self.entry_points:
            del self.entry_points[(group, name)]
            return

        self.entry_points[(group, name)] = f"runtime_models_{self.model.base_name}{separator}{value}"

    _not_found_messages = MappingProxyType(
        {
            BuilderClass: "Builder class",
            BuilderClassList: "Builder class list",
            BuilderList: "Builder list",
            BuilderDict: "Builder dictionary",
            BuilderModule: "Builder module",
        },
    )

    def _get[T](self, name: str, clz: type[T]) -> T:
        """Get a partial by name."""
        if name not in self.partials:
            raise PartialNotFoundError(
                f"{self._not_found_messages[clz]} {name} not found.",  # type: ignore # noqa
            )
        partial = self.partials[name]
        if not isinstance(partial, clz):
            raise TypeError(f"Partial {name} is not a {clz.__name__}.")
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

        for partial in self.partials.values():
            if not isinstance(partial, BuilderFile):
                continue

            self.ns.__files__[f"{partial.module_name}/{partial.file_path}"] = partial.content

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
