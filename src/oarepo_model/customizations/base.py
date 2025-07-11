#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import logging
import traceback
from typing import TYPE_CHECKING

log = logging.getLogger("oarepo_model")

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class Customization:
    """Base class for customizations in Oarepo models.

    Customizations can be used to modify the behavior of the model.
    """

    def __init__(self, name) -> None:
        # name of the variable that this customization modified
        self.name = name
        self._created_from = None
        if log.isEnabledFor(logging.DEBUG):
            self._created_from = get_stack_without_customizations(2)
        else:
            self._created_from = None

    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        """Apply the customization to the given model."""
        raise NotImplementedError("Subclasses must implement this method.")

    def __repr__(self):
        return f"<Customization {self.__class__.__name__} {self._created_from or ''}>"


def get_stack_without_customizations(ignore_top: int = 0):
    """Get the stack trace without customizations."""
    stack = traceback.extract_stack()[: -(ignore_top + 1)]
    return (
        f"{stack[-1].filename}:{stack[-1].lineno} in {stack[-1].name}"
        if stack
        else "No stack trace available"
    )
