# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""The typing-only Ext protocols must stay out of the runtime MRO of composed Ext classes."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from oarepo_model.presets.records_resources.ext import RecordExtensionProtocol, RecordExtensionProtocolTyping
from oarepo_model.presets.records_resources.ext_files import (
    RecordWithFilesExtensionProtocol,
    RecordWithFilesExtensionProtocolTyping,
)

if TYPE_CHECKING:
    from flask import Flask


def test_public_protocol_names_are_runtime_transparent():
    """Presets outside this package use these names as real bases, eg. oarepo-rdm's ExtRDMMixin."""
    assert RecordExtensionProtocol is object
    assert RecordWithFilesExtensionProtocol is object


def test_typing_protocols_contribute_no_runtime_members():
    """Even when subclassed directly, they must not shadow the real implementations."""
    for member in ("model_arguments", "records_service_params", "init_config"):
        assert member not in vars(RecordExtensionProtocolTyping)
    assert "files_service" not in vars(RecordWithFilesExtensionProtocolTyping)


def test_mixin_inheriting_the_public_name_does_not_cut_the_init_config_chain():
    """The bottom of the chain is ExtBase, which registers the model in OAREPO_MODELS."""
    calls: list[str] = []

    class ExtBase:
        def init_config(self, app: Flask) -> None:
            calls.append("ext_base")

    class FeatureMixin(RecordExtensionProtocol):
        def init_config(self, app: Flask) -> None:
            super().init_config(app)
            calls.append("mixin")

    type("Ext", (FeatureMixin, ExtBase), {})().init_config(MagicMock())

    assert calls == ["ext_base", "mixin"]


def test_mixin_inheriting_the_public_name_does_not_cut_the_model_arguments_chain():
    class ExtBase:
        @property
        def model_arguments(self) -> dict[str, object]:
            return {"base": True}

    class FeatureMixin(RecordExtensionProtocol):
        @property
        def model_arguments(self) -> dict[str, object]:
            return {**super().model_arguments, "mixin": True}

    ext = type("Ext", (FeatureMixin, ExtBase), {})()

    assert ext.model_arguments == {"base": True, "mixin": True}
