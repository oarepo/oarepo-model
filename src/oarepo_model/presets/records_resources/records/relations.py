# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Module that creates a relations dictionary in the model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import AddDictionary, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RelationsPreset(Preset):
    """Preset that adds "relations" dictionary to the model.

    If you want to add a custom relation, call:

    ```python
        from oarepo_model.customizations import AddToDictionary

        AddToDictionary("relations", key, value)
    ```
    in your preset or customizations array.
    """

    provides = ("relations",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddDictionary("relations", {})
