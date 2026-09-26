# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Tests for UIExtPreset's ui_blueprint_name handling."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from oarepo_model.presets.ui.ui_ext import UIExtPreset


def _ext_model_arguments(configuration: dict[str, Any]) -> dict[str, Any]:
    """Compose the preset's ExtUIMixin over a base Ext and return its model_arguments."""
    builder = SimpleNamespace(runtime_dependencies={"ui_model": {"ui": "model"}})
    [customization] = UIExtPreset().apply(builder, SimpleNamespace(configuration=configuration), {})
    ext_uimixin = customization.clazz

    class ExtBase:
        @property
        def model_arguments(self) -> dict[str, Any]:
            return {"base": True}

    ext = type("Ext", (ext_uimixin, ExtBase), {})()
    return ext.model_arguments


def test_ui_blueprint_name_is_omitted_when_not_configured():
    """An unset ui_blueprint_name must be absent, not the string 'None'."""
    args = _ext_model_arguments({})
    assert "ui_blueprint_name" not in args
    assert args["ui_model"] == {"ui": "model"}


def test_ui_blueprint_name_is_omitted_when_falsy():
    args = _ext_model_arguments({"ui_blueprint_name": ""})
    assert "ui_blueprint_name" not in args


def test_ui_blueprint_name_is_passed_through_when_set():
    args = _ext_model_arguments({"ui_blueprint_name": "test_ui"})
    assert args["ui_blueprint_name"] == "test_ui"
