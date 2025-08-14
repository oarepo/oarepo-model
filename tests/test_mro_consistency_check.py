#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import pytest

from oarepo_model.c3linearize import LinearizationError, mro_without_class_construction


def test_mro_consistency_check():
    class X:
        pass

    class Y:
        pass

    class A(X, Y):
        pass

    B = type("B", (Y, X), {})
    b_mro = mro_without_class_construction([Y, X])
    assert b_mro == B.mro()[1:]

    with pytest.raises(TypeError):
        type("inconsistent", (A, B), {})
    with pytest.raises(LinearizationError):
        mro_without_class_construction([A, B])
