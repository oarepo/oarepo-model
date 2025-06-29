from __future__ import annotations

from typing import TYPE_CHECKING

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

    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        """Apply the customization to the given model."""
        raise NotImplementedError("Subclasses must implement this method.")

    def __repr__(self):
        return f"<Customization {self.__class__.__name__}>"
