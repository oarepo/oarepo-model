#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations.change_base import ReplaceBaseClass
from oarepo_model.errors import BaseClassNotFoundError


class OldBase:
    """Old base class for testing."""


class NewBase:
    """New base class for testing."""


class SubclassOfOld(OldBase):
    """Subclass of OldBase for testing."""


class UnrelatedBase:
    """Unrelated base class for testing."""


def test_replace_base_class_success():
    """Test successful replacement of a base class."""
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    clz = builder.add_class("TestClass")
    clz.add_base_classes(OldBase, UnrelatedBase)

    ReplaceBaseClass("TestClass", OldBase, NewBase).apply(builder, model)

    clz = builder.get_class("TestClass")
    assert NewBase in clz.base_classes
    assert OldBase not in clz.base_classes
    assert UnrelatedBase in clz.base_classes


def test_replace_base_class_not_found_with_fail():
    """Test that an error is raised when base class is not found and fail=True."""
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    clz = builder.add_class("TestClass")
    clz.add_base_classes(UnrelatedBase)

    with pytest.raises(BaseClassNotFoundError, match="Base class OldBase not found"):
        ReplaceBaseClass("TestClass", OldBase, NewBase, fail=True).apply(builder, model)


def test_replace_base_class_not_found_without_fail():
    """Test that no error is raised when base class is not found and fail=False."""
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    clz = builder.add_class("TestClass")
    clz.add_base_classes(UnrelatedBase)

    # This should not raise an error
    ReplaceBaseClass("TestClass", OldBase, NewBase, fail=False).apply(builder, model)

    # Base classes should remain unchanged
    clz = builder.get_class("TestClass")
    assert UnrelatedBase in clz.base_classes
    assert OldBase not in clz.base_classes
    assert NewBase not in clz.base_classes


def test_replace_base_class_with_subclass_matching():
    """Test replacement with subclass matching enabled."""
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    clz = builder.add_class("TestClass")
    clz.add_base_classes(SubclassOfOld, UnrelatedBase)

    ReplaceBaseClass("TestClass", OldBase, NewBase, subclass=True).apply(builder, model)

    clz = builder.get_class("TestClass")
    assert NewBase in clz.base_classes
    assert SubclassOfOld not in clz.base_classes
    assert UnrelatedBase in clz.base_classes


def test_replace_base_class_without_subclass_matching():
    """Test that subclass is not replaced when subclass matching is disabled."""
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    clz = builder.add_class("TestClass")
    clz.add_base_classes(SubclassOfOld, UnrelatedBase)

    with pytest.raises(BaseClassNotFoundError, match="Base class OldBase not found"):
        ReplaceBaseClass("TestClass", OldBase, NewBase, subclass=False, fail=True).apply(builder, model)


def test_replace_base_class_already_built():
    """Test that an error is raised when trying to replace base class after building."""
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    clz = builder.add_class("TestClass")
    clz.add_base_classes(OldBase)
    clz.built = True

    with pytest.raises(RuntimeError, match="Cannot change base class"):
        ReplaceBaseClass("TestClass", OldBase, NewBase).apply(builder, model)
