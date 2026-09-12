# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Base class for all model customizations.

This module provides the abstract Customization base class that defines the
interface for all model customizations in OARepo. Customizations are used to
modify the behavior and structure of models during the build process.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel

log = logging.getLogger("oarepo_model")

#: customization classes already warned about the deprecated name-based fallback
_modifies_fallback_warned: set[str] = set()


class Customization:
    """Base class for customizations in Oarepo models.

    Customizations can be used to modify the behavior of the model.
    """

    #: set by subclasses that modify the partial passed in as their constructor
    #: `name`; for fixed partial names declare `modifies` instead, and for any other
    #: per-instance case override the `modifies` property
    modifies_own_name: bool = False

    def __init__(self, name: str) -> None:
        """Initialize the customization."""
        # name of the variable that this customization creates/uses/modifies
        self.name = name

    @property
    def modifies(self) -> tuple[str, ...]:
        """Partials this customization modifies.

        Used to order the customization against presets: it is applied before the first
        preset that declares any of these partials in its depends_on. Subclasses must
        declare them explicitly - as a class attribute for fixed partial names, via
        `modifies_own_name = True` when the partial is the constructor-given name, or by
        overriding this property for any other per-instance case. Falling back to
        (self.name,) without any declaration is deprecated and will be removed in a
        future version.
        """
        cls = type(self)
        if not cls.modifies_own_name and cls.__qualname__ not in _modifies_fallback_warned:
            _modifies_fallback_warned.add(cls.__qualname__)
            log.warning(
                "%s.modifies falls back to the deprecated name-based default (%r);"
                " declare the modified partials explicitly",
                cls.__qualname__,
                self.name,
            )
        return (self.name,)

    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        """Apply the customization to the given model."""
        raise NotImplementedError(  # pragma: no cover
            "Subclasses must implement this method."
        )

    @override
    def __repr__(self):
        return f"<Customization {self.__class__.__name__} {self.name!r}>"
