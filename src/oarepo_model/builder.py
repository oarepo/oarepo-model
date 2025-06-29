from importlib.metadata import EntryPoint
from types import SimpleNamespace
from typing import Any, cast

from werkzeug.local import LocalProxy

from oarepo_model.errors import AlreadyRegisteredError, PartialNotFoundError

from .model import InvenioModel, RuntimeDependencies
from .utils import (
    is_mro_consistent,
    make_mro_consistent,
)


class Partial:
    def __init__(self, key: str):
        self.key = key

    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> Any:
        """Build the class from the partial."""
        raise NotImplementedError("Subclasses must implement this method.")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(key={self.key})"


class BuilderClass(Partial):
    def __init__(
        self,
        class_name: str,
        mixins: list[type] | None = None,
        base_classes: list[type] | None = None,
    ):
        super().__init__(key=class_name)
        self.class_name = class_name
        self.mixins = list(mixins) if mixins else []
        self.base_classes = list(base_classes) if base_classes else []

    def add_base_classes(self, *classes: type) -> None:
        """Add base classes to the class."""
        self.base_classes.extend(classes)

    def add_mixins(self, *classes: type) -> None:
        """Add mixins to the class."""
        for clazz in reversed(classes):
            self.mixins.insert(0, clazz)  # Prepend to preserve MRO

    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> type:
        base_list: list[type] = [
            *self.mixins,
            *self.base_classes,
        ]
        if not is_mro_consistent(base_list):
            # If the MRO is not consistent, we need to make it consistent
            base_list = make_mro_consistent(base_list)

        return type(
            self.class_name,
            tuple(base_list),
            {
                "__module__": type(self).__module__,
                "__qualname__": self.class_name,
                "oarepo_model": model,
                "oarepo_model_namespace": namespace,
            },
        )


class BuilderClassList(Partial, list[type]):
    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> list[type]:
        if not is_mro_consistent(self):
            # If the MRO is not consistent, we need to make it consistent
            return make_mro_consistent(self)
        return list(self)


class BuilderList(Partial, list[Any]):
    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> list[Any]:
        return list(self)


class BuilderDict(Partial, dict[str, Any]):
    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> dict[str, Any]:
        """Build a dictionary from the partial."""
        return {k: v for k, v in self.items() if v is not None}


class BuilderModule(Partial, SimpleNamespace):
    def build(self, model: InvenioModel, namespace: SimpleNamespace) -> Any:
        """Build a module from the partial."""

        # iterate through all attributes of the simple namespace and
        # if any of those has a __get__ method, call it. This will handle
        # Dependency descriptors and other similar cases.
        ret = SimpleNamespace()
        for attr in self.__dict__:
            try:
                if attr.startswith("_") and attr != "__file__":
                    continue
                value = getattr(self, attr)
                if (
                    callable(value)
                    and not isinstance(value, LocalProxy)
                    and hasattr(value, "__get__")
                ):
                    value = value.__get__(self, type(self))
                setattr(ret, attr, value)
            except Exception as e:
                raise RuntimeError(
                    f"Error while building module {self.key} attribute {attr}: {e}"
                ) from e
        return ret

    def __setitem__(self, key: str, value: Any) -> None:
        """Simulate a dictionary's x["key"] = value."""
        setattr(self, key, value)


class InvenioModelBuilder:
    def __init__(self, model: InvenioModel):
        self.model = model
        self.ns = SimpleNamespace()
        self.partials: dict[str, Partial] = {}
        self.entry_points: dict[tuple[str, str], str] = {}
        self.runtime_dependencies = RuntimeDependencies()

    def add_class(
        self, name: str, clazz: type | None = None, exists_ok: bool = False
    ) -> BuilderClass:
        """Add a class to the builder."""
        if name in self.partials:
            if exists_ok:
                return cast(BuilderClass, self.partials[name])
            raise AlreadyRegisteredError(f"Class {name} already exists.")
        self.partials[name] = clz = BuilderClass(
            self.model.title_name + name.title().replace("_", ""),
            base_classes=[clazz] if clazz else [],
        )
        return clz

    def get_class(self, name: str) -> BuilderClass:
        """Get a class by name."""
        return self._get(name, BuilderClass)

    def add_class_list(
        self, name: str, *classes: type, exists_ok: bool = False
    ) -> BuilderClassList:
        if name in self.partials:
            if exists_ok:
                return cast(BuilderClassList, self.partials[name])
            raise AlreadyRegisteredError(f"Class list {name} already exists.")
        self.partials[name] = cll = BuilderClassList(name)
        cll.extend(classes)
        return cll

    def get_class_list(self, name: str) -> BuilderClassList:
        """Get a class list by name."""
        return self._get(name, BuilderClassList)

    def add_list(
        self, name: str, *classes: type, exists_ok: bool = False
    ) -> BuilderList:
        if name in self.partials:
            if exists_ok:
                return cast(BuilderList, self.partials[name])
            raise AlreadyRegisteredError(f"List {name} already exists.")
        self.partials[name] = cll = BuilderList(name)
        cll.extend(classes)
        return cll

    def get_list(self, name: str) -> BuilderList:
        """Get a list by name."""
        return self._get(name, BuilderList)

    def add_dictionary(
        self, name: str, default: dict[str, Any] | None = None, exists_ok: bool = False
    ) -> BuilderDict:
        """Add a dictionary to the builder."""
        if name in self.partials:
            if exists_ok:
                return cast(BuilderDict, self.partials[name])
            raise AlreadyRegisteredError(f"Dictionary {name} already exists.")
        self.partials[name] = ret = BuilderDict(name)
        ret.update(default or {})
        return ret

    def get_dictionary(self, name: str) -> dict[str, Any]:
        """Get a dictionary by name."""
        return self._get(name, BuilderDict)

    def add_module(self, name: str, exists_ok: bool = False) -> BuilderModule:
        """Add a module to the builder."""
        if name in self.partials:
            if exists_ok:
                return cast(BuilderModule, self.partials[name])
            raise AlreadyRegisteredError(f"Module {name} already exists.")
        self.partials[name] = _module = BuilderModule(name)
        return _module

    def get_module(self, name: str) -> BuilderModule:
        return self._get(name, BuilderModule)

    def add_entry_point(
        self,
        group: str,
        name: str,
        value: str,
        overwrite: bool = False,
        separator: str = ":",
    ) -> None:
        """Add an entry point to the builder."""
        if (group, name) in self.entry_points and not overwrite:
            raise AlreadyRegisteredError(f"Entry point {group}:{name} already exists.")
        if value is None and (group, name) in self.entry_points:
            del self.entry_points[(group, name)]
            return
        self.entry_points[(group, name)] = (
            f"runtime_models_{self.model.base_name}{separator}{value}"
        )

    _not_found_messages = {
        BuilderClass: "Builder class",
        BuilderClassList: "Builder class list",
        BuilderList: "Builder list",
        BuilderDict: "Builder dictionary",
        BuilderModule: "Builder module",
    }

    def _get[T](self, name: str, clz: type[T]) -> T:
        """Get a partial by name."""
        if name not in self.partials:
            raise PartialNotFoundError(
                f"{self._not_found_messages[clz]} {name} not found."
            )
        partial = self.partials[name]
        assert isinstance(partial, clz), f"Partial {name} is not a {clz.__name__}."
        return partial

    def get_runtime_dependencies(self):
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

    def build(self) -> SimpleNamespace:
        for key in self.partials.keys():
            self.build_partial(key)

        # TODO: need to have entry points separate from the partials ???
        entry_points = []
        for group, name in self.entry_points:
            value = self.entry_points[(group, name)]
            entry_points.append(EntryPoint(group=group, name=name, value=value))

        self.ns.entry_points = entry_points
        self.runtime_dependencies.bind_dependencies(self.ns)
        return self.ns
