# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Mutations of class partials must fail loudly once the partial has been built.

A preset that misses the class partial in its `modifies` used to lose the field or the base class
silently, because api.py eagerly builds every `depends_on` partial before the preset runs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from invenio_records_permissions.policies.records import RecordPermissionPolicy

from oarepo_model.api import model
from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations import AddBaseClass, AddClassField
from oarepo_model.customizations.high_level.set_permission_policy import SetPermissionPolicy
from oarepo_model.errors import ApplyCustomizationError
from oarepo_model.presets.base import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.customizations import Customization
    from oarepo_model.model import InvenioModel


class Base:
    """Base class used by the tests."""


class Other(Base):
    """Another base class used by the tests."""


class Policy(RecordPermissionPolicy):
    """Permission policy used by the tests."""


def _builder() -> InvenioModelBuilder:
    model = MagicMock()
    model.title_name = "Test"
    return InvenioModelBuilder(model, MagicMock())


def _builder_with_built_class() -> InvenioModelBuilder:
    builder = _builder()
    builder.add_class("TestClass", Base)
    builder.build_partial("TestClass")
    return builder


def test_add_class_field_before_build():
    builder = _builder()
    builder.add_class("TestClass", Base)

    AddClassField("TestClass", "table", "record").apply(builder, MagicMock())

    assert builder.get_class("TestClass").fields["table"] == "record"


def _policy_builder() -> InvenioModelBuilder:
    """Builder with a PermissionPolicy class that already carries one mixin."""
    builder = _builder()
    builder.add_class("PermissionPolicy", Base)
    builder.get_class("PermissionPolicy").add_mixins(Other)
    return builder


def test_add_class_field_after_build_raises():
    builder = _builder_with_built_class()

    with pytest.raises(RuntimeError, match="Cannot add fields after the class is built"):
        AddClassField("TestClass", "table", "record").apply(builder, MagicMock())


def test_add_base_class_after_build_raises():
    builder = _builder_with_built_class()

    with pytest.raises(RuntimeError, match="Cannot add base classes after the class is built"):
        AddBaseClass("TestClass", Other).apply(builder, MagicMock())


def test_set_permission_policy_before_build():
    builder = _policy_builder()

    SetPermissionPolicy(Policy).apply(builder, MagicMock())

    policy = builder.get_class("PermissionPolicy")
    assert policy.base_classes == [Policy]
    assert policy.mixins == []


def test_set_permission_policy_keeps_mixins():
    builder = _policy_builder()

    SetPermissionPolicy(Policy, keep_mixins=True).apply(builder, MagicMock())

    policy = builder.get_class("PermissionPolicy")
    assert policy.base_classes == [Policy]
    assert policy.mixins == [Other]


def test_set_permission_policy_after_build_raises():
    builder = _policy_builder()
    builder.build_partial("PermissionPolicy")

    with pytest.raises(RuntimeError, match="Cannot set base classes after the class is built"):
        SetPermissionPolicy(Policy).apply(builder, MagicMock())


class ProvidesClass(Preset):
    """Preset that creates a class partial."""

    provides = ("records",)

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, object],
    ) -> Generator[Customization]:
        """Create the class partial."""
        builder.add_class("records", Base)
        yield from ()


class MisdeclaredField(Preset):
    """Preset that writes a field into the class while only depending on it."""

    depends_on = ("records",)

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, object],
    ) -> Generator[Customization]:
        """Add a field to the class."""
        yield AddClassField("records", "table", "record")


def test_depends_on_builds_the_class_early_so_mutation_is_not_silent():
    """The `depends_on` partial is built before the preset runs, so the field cannot be added.

    Before the guarded API this lost the field without any complaint.
    """
    with pytest.raises(ApplyCustomizationError, match="Cannot add fields after the class is built"):
        model(
            name="misdeclared_field",
            version="1.0.0",
            presets=[ProvidesClass, MisdeclaredField],
            types=[],
            metadata_type="Metadata",
        )
