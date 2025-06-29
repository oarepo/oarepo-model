#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
import dataclasses
from types import SimpleNamespace
from typing import Any, Callable


@dataclasses.dataclass
class InvenioModel:
    name: str
    version: str
    description: str
    configuration: dict[str, Any]

    @property
    def base_name(self) -> str:
        """Return the base name of the model."""
        if "base_name" in self.configuration:
            return self.configuration["base_name"]
        return self.name.lower().replace(" ", "_").replace("-", "_")

    @property
    def slug(self) -> str:
        """Return a slugified version of the model name."""
        if "slug" in self.configuration:
            return self.configuration["slug"]
        return self.base_name.replace("_", "-")

    @property
    def title_name(self) -> str:
        """Return the title case version of the model name."""
        if "title_name" in self.configuration:
            return self.configuration["title_name"]
        return self.base_name.title().replace("_", " ").replace("-", " ")


class CachedDescriptor:
    """A descriptor that caches the value in the instance or class."""

    attr: str

    def __set_name__(self, owner: type, name: str) -> None:
        try:
            super().__set_name__(owner, name)
        except AttributeError:
            # If the superclass does not have __set_name__, we set the attribute directly
            pass
        self.attr = name

    def __get__(self, instance: InvenioModel, owner: type) -> Any:
        if instance and hasattr(instance, f"_cached_{self.attr}"):
            ret = getattr(instance, f"_cached_{self.attr}")[0]
        elif owner and hasattr(owner, f"_cached_{self.attr}"):
            ret = getattr(owner, f"_cached_{self.attr}")[0]
        else:
            if instance is None:
                oarepo_model = owner.oarepo_model
                oarepo_model_namespace = owner.oarepo_model_namespace
            else:
                oarepo_model = instance.oarepo_model
                oarepo_model_namespace = instance.oarepo_model_namespace

            ret = self.real_get_value(
                instance, owner, oarepo_model, oarepo_model_namespace
            )
            if instance is None:
                setattr(owner, f"_cached_{self.attr}", [ret])
            else:
                setattr(instance, f"_cached_{self.attr}", [ret])

        if hasattr(ret, "__get__"):
            # If the return value is a descriptor, we need to call it
            ret = ret.__get__(instance, owner)

        return ret

    def real_get_value(
        self,
        instance: InvenioModel,
        owner: type,
        oarepo_model: InvenioModel,
        target_namespace: SimpleNamespace,
    ) -> Any:
        """Override this method to provide the actual value."""
        raise NotImplementedError("Subclasses must implement real_get_value method.")


class FromModelConfiguration[T](CachedDescriptor):
    def __init__(self, key: str, default: T | None = None) -> None:
        self.key = key
        self.default = default

    def real_get_value(
        self,
        instance: InvenioModel,
        owner: type,
        oarepo_model: InvenioModel,
        target_namespace: SimpleNamespace,
    ) -> T:
        return oarepo_model.configuration.get(self.key, self.default)


class FromModel[T](CachedDescriptor):
    def __init__(self, callback: Callable[[InvenioModel], T]) -> None:
        self.callback = callback

    def real_get_value(
        self,
        instance: InvenioModel,
        owner: type,
        oarepo_model: InvenioModel,
        target_namespace: SimpleNamespace,
    ) -> T:
        return self.callback(oarepo_model)


class AddToList[T](CachedDescriptor):
    def __init__(self, *data: T, position: int = -1) -> None:
        self.data = list(data)
        self.position = position

    def real_get_value(
        self,
        instance: InvenioModel,
        owner: type,
        oarepo_model: InvenioModel,
        target_namespace: SimpleNamespace,
    ) -> list[T]:
        if instance is None:
            super_value = owner.mro()[1].__getattribute__(self.attr)
        else:
            super_value = super(instance.__class__, instance).__getattribute__(
                self.attr
            )

        if super_value is None:
            return self.data

        if not isinstance(super_value, (tuple, list)):
            raise TypeError(f"Expected a list for {self.attr}, got {type(super_value)}")

        if isinstance(super_value, tuple):
            super_value = list(super_value)

        if self.position < 0:
            return super_value + list(self.data)
        else:
            return (
                super_value[: self.position]
                + list(self.data)
                + super_value[self.position :]
            )


MISSING = object()


class Dependency(CachedDescriptor):
    def __init__(
        self,
        *keys: str,
        transform: Callable[..., Any] | None = None,
        default: Any = MISSING,
    ) -> None:
        self.keys = keys
        assert self.keys, "At least one key must be provided for Dependency"
        self.transform = transform
        self.default = default

    def real_get_value(
        self,
        instance: InvenioModel,
        owner: type,
        oarepo_model: InvenioModel,
        target_namespace: SimpleNamespace,
    ) -> Any:
        ret = []
        default: list | tuple
        if len(self.keys) == 1 or not isinstance(self.default, (list, tuple)):
            default = [self.default]
        else:
            default = self.default

        for idx, key in enumerate(self.keys):
            if not hasattr(target_namespace, key):
                if idx < len(default) and default[idx] is not MISSING:
                    ret.append(default[idx])
                else:
                    raise AttributeError(
                        f"Model {oarepo_model.name} does not have attribute '{key}'"
                    )
            else:
                ret.append(getattr(target_namespace, key))

        if self.transform is not None:
            return self.transform(*ret)

        if len(ret) == 1:
            return ret[0]
        return ret


class ModelMixin:
    oarepo_model_namespace: Any

    def get_model_dependency(self, key: str) -> Any:
        """Get a dependency by key."""
        return getattr(self.oarepo_model_namespace, key)


class RuntimeDependencies:
    """A class to hold bound dependencies for a model."""

    def __init__(self) -> None:
        self.dependencies: SimpleNamespace | None = None

    def bind_dependencies(self, dependencies: SimpleNamespace) -> None:
        """
        Bind dependencies to the model.
        """
        self.dependencies = dependencies

    def get(self, key: str) -> Any:
        """
        Get a bound dependency by key.

        :param key: The key of the dependency to get.
        :return: The value of the dependency.
        """
        if self.dependencies is None:
            raise ValueError("Dependencies are not bound yet.")
        return getattr(self.dependencies, key)
