#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Core model classes and data structures for OARepo models.

This module contains the fundamental data classes and structures that represent
OARepo models, including model metadata, configuration, and runtime dependencies.
"""

from __future__ import annotations

import dataclasses
from contextlib import suppress
from typing import TYPE_CHECKING, Any, cast, override

from .utils import title_case

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import SimpleNamespace


@dataclasses.dataclass
class InvenioModel:
    """A class representing an Invenio model with metadata and configuration."""

    name: str
    version: str
    description: str
    configuration: dict[str, Any]
    metadata_type: str | None = None
    record_type: str | None = None

    @property
    def base_name(self) -> str:
        """Return the base name of the model."""
        if "base_name" in self.configuration:
            return cast("str", self.configuration["base_name"])
        return self.name.lower().replace(" ", "_").replace("-", "_")

    @property
    def slug(self) -> str:
        """Return a slugified version of the model name."""
        if "slug" in self.configuration:
            return cast("str", self.configuration["slug"])
        return self.base_name.replace("_", "-")

    @property
    def title_name(self) -> str:
        """Return the title case version of the model name."""
        if "title_name" in self.configuration:
            return cast("str", self.configuration["title_name"])
        return title_case(self.base_name)

    @property
    def uppercase_name(self) -> str:
        """Return the uppercase version of the model name."""
        if "uppercase_name" in self.configuration:
            return cast("str", self.configuration["uppercase_name"])
        return self.name.upper().replace(" ", "_").replace("-", "_")

    @property
    def in_memory_package_name(self) -> str:
        """Return the in-memory package name for the model."""
        return f"runtime_models_{self.base_name}"

    @property
    def blueprint_base(self) -> str:
        """Return the blueprint base name for the model."""
        return self.base_name


class CachedDescriptor:
    """A descriptor that caches the value in the instance or class."""

    attr: str

    def __set_name__(self, owner: type, name: str) -> None:
        """Set the name of the attribute and initialize the cache."""
        with suppress(AttributeError):
            super().__set_name__(owner, name)  # type: ignore[misc]
        self.attr = name

    def __get__(self, instance: ModelMixin | None, owner: type[ModelMixin]) -> Any:
        """Get the cached value or compute it if not cached."""
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
                instance,
                owner,
                oarepo_model,
                oarepo_model_namespace,
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
        instance: ModelMixin | None,
        owner: type[ModelMixin],
        oarepo_model: InvenioModel,
        target_namespace: SimpleNamespace,
    ) -> Any:
        """Override this method to provide the actual value."""
        raise NotImplementedError("Subclasses must implement real_get_value method.")


class FromModelConfiguration[T](CachedDescriptor):
    """A descriptor that retrieves a value from the InvenioModel configuration."""

    def __init__(self, key: str, default: T | None = None) -> None:
        """Initialize the FromModelConfiguration descriptor."""
        self.key = key
        self.default = default

    @override
    def real_get_value(
        self,
        instance: ModelMixin | None,
        owner: type[ModelMixin],
        oarepo_model: InvenioModel,
        target_namespace: SimpleNamespace,
    ) -> Any:
        return oarepo_model.configuration.get(self.key, self.default)


class FromModel[T](CachedDescriptor):
    """A descriptor that retrieves a value from the InvenioModel."""

    def __init__(self, callback: Callable[[InvenioModel], T]) -> None:
        """Initialize the FromModel descriptor with a callback."""
        self.callback = callback

    @override
    def real_get_value(
        self,
        instance: ModelMixin | None,
        owner: type[ModelMixin],
        oarepo_model: InvenioModel,
        target_namespace: SimpleNamespace,
    ) -> T:
        return self.callback(oarepo_model)


class AddToList[T](CachedDescriptor):
    """A descriptor that adds items to a list at a specific position."""

    def __init__(self, *data: T, position: int = -1) -> None:
        """Initialize the AddToList descriptor."""
        self.data = list(data)
        self.position = position

    @override
    def real_get_value(
        self,
        instance: ModelMixin | None,
        owner: type[ModelMixin],
        oarepo_model: InvenioModel,
        target_namespace: SimpleNamespace,
    ) -> list[T]:
        if instance is None:
            super_value = owner.mro()[1].__getattribute__(self.attr)
        else:
            super_value = super(instance.__class__, instance).__getattribute__(
                self.attr,
            )

        if super_value is None:
            return self.data

        if not isinstance(super_value, (tuple, list)):
            raise TypeError(f"Expected a list for {self.attr}, got {type(super_value)}")

        if isinstance(super_value, tuple):
            super_value = list(super_value)

        if self.position < 0:
            return super_value + list(self.data)
        return super_value[: self.position] + list(self.data) + super_value[self.position :]


MISSING = object()


class Dependency(CachedDescriptor):
    """A descriptor for model dependencies."""

    def __init__(
        self,
        *keys: str,
        transform: Callable[..., Any] | None = None,
        default: Any = MISSING,
    ) -> None:
        """Initialize the Dependency descriptor."""
        self.keys = keys
        if not keys:
            raise ValueError("At least one key must be provided for Dependency")
        self.transform = transform
        self.default = default

    @override
    def real_get_value(
        self,
        instance: ModelMixin | None,
        owner: type[ModelMixin],
        oarepo_model: InvenioModel,
        target_namespace: SimpleNamespace,
    ) -> Any:
        ret = []
        default: list | tuple
        default = [self.default] if len(self.keys) == 1 or not isinstance(self.default, (list, tuple)) else self.default

        for idx, key in enumerate(self.keys):
            if not hasattr(target_namespace, key):
                if idx < len(default) and default[idx] is not MISSING:
                    ret.append(default[idx])
                else:
                    raise AttributeError(
                        f"Model {oarepo_model.name} does not have attribute '{key}'",
                    )
            else:
                ret.append(getattr(target_namespace, key))

        if self.transform is not None:
            return self.transform(*ret)

        if len(ret) == 1:
            if ret[0] is None:
                raise ValueError(
                    f"Dependency {self.keys[0]} is None, but expected a value.",
                )
            return ret[0]
        return ret


class ModelMixin:
    """A mixin class for InvenioModel that provides access to the model and its namespace."""

    oarepo_model_namespace: Any
    oarepo_model: InvenioModel

    def get_model_dependency(self, key: str) -> Any:
        """Get a dependency by key."""
        return getattr(self.oarepo_model_namespace, key)


class RuntimeDependencies:
    """A class to hold bound dependencies for a model."""

    def __init__(self) -> None:
        """Initialize the RuntimeDependencies with an empty namespace."""
        self.dependencies: SimpleNamespace | None = None

    def bind_dependencies(self, dependencies: SimpleNamespace) -> None:
        """Bind dependencies to the model."""
        self.dependencies = dependencies

    def get(self, key: str) -> Any:
        """Get a bound dependency by key.

        :param key: The key of the dependency to get.
        :return: The value of the dependency.
        """
        if self.dependencies is None:
            raise ValueError("Dependencies are not bound yet.")
        ret = getattr(self.dependencies, key)
        if ret is None:
            raise ValueError(f"Dependency {key} is None, but expected a value.")
        return ret
