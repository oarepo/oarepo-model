#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from oarepo_model.customizations import AddDictionary, Customization
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class RelationsPreset(Preset):
    """
    Preset that adds "relations" dictionary to the model. If you want to add
    a custom relation, call:

    ```python
        from oarepo_model.customizations import AddToDictionary

        AddToDictionary("relations", key, value)
    ```
    in your preset or customizations array.
    """

    provides = [
        "relations",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:

        yield AddDictionary("relations", {})
