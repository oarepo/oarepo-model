# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Base class for all model customizations.

This module provides the abstract Customization base class that defines the
interface for all model customizations in OARepo. Customizations are used to
modify the behavior and structure of models during the build process.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class Customization:
    """Base class for customizations in Oarepo models.

    Customizations can be used to modify the behavior of the model.
    """

    def __init__(self, name: str) -> None:
        """Initialize the customization."""
        # name of the variable that this customization creates/uses/modifies
        self.name = name

    @property
    def modifies(self) -> tuple[str, ...]:
        """Partials this customization modifies.

        Used to order the customization against presets: it is applied before the first
        preset that declares any of these partials in its depends_on. Subclasses that
        target a different partial than their name must declare it as a class attribute.
        """
        return (self.name,)

    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        """Apply the customization to the given model."""
        raise NotImplementedError(  # pragma: no cover
            "Subclasses must implement this method."
        )

    @override
    def __repr__(self):
        return f"<Customization {self.__class__.__name__}>"  # pragma: no cover
