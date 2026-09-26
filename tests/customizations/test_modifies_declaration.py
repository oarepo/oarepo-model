# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

import logging

from oarepo_model.customizations import AddToList, Customization


class Undeclared(Customization):
    """Customization that relies on the deprecated name-based modifies fallback."""

    def apply(self, builder, model) -> None:
        """Do nothing."""


def test_modifies_fallback_logs_deprecation_warning(caplog) -> None:
    with caplog.at_level(logging.WARNING, logger="oarepo_model"):
        assert Undeclared("X").modifies == ("X",)
        # the warning is logged once per class
        assert Undeclared("Y").modifies == ("Y",)

    warnings = [r for r in caplog.records if "modifies falls back" in r.message]
    assert len(warnings) == 1
    assert "Undeclared" in warnings[0].getMessage()


def test_declared_modifies_do_not_warn(caplog) -> None:
    with caplog.at_level(logging.WARNING, logger="oarepo_model"):
        assert AddToList("AList", "item").modifies == ("AList",)

    assert not [r for r in caplog.records if "modifies falls back" in r.message]
