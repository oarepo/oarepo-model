# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""High-level customization for adding search parameter interpreters to models.

This module provides the AddParamInterpreterCls customization that registers
an extra search parameter interpreter class on the record search options.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..add_to_list import AddToList

if TYPE_CHECKING:
    from invenio_records_resources.services.records.params.base import ParamInterpreter


class AddParamInterpreterCls(AddToList):
    """Customization to add an extra search parameter interpreter class to the model."""

    def __init__(self, clazz: type[ParamInterpreter]):
        """Initialize the AddParamInterpreterCls customization."""
        super().__init__("extra_param_interpreter_classes", clazz)
