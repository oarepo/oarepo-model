#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""High-level customization for adding search parameter interpreters to models.

This module provides the AddParamInterpreterCls customization that registers
an extra search parameter interpreter class on the record search options.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ..base import Customization

if TYPE_CHECKING:
    from invenio_records_resources.services.records.params.base import ParamInterpreter

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddParamInterpreterCls(Customization):
    """Customization to add an extra search parameter interpreter class to the model."""

    modifies = ("extra_param_interpreter_classes",)

    def __init__(self, clazz: type[ParamInterpreter]):
        """Initialize the AddParamInterpreterCls customization."""
        super().__init__("AddParamInterpreterCls")
        self._clazz = clazz

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        interpreter_classes = builder.get_list("extra_param_interpreter_classes")
        interpreter_classes.append(self._clazz)
