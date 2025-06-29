from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddToModule(Customization):
    """Customization to add a property to a module to the model."""

    def __init__(
        self,
        module_name: str,
        property_name: str,
        value: Any,
        exists_ok: bool = False,
    ) -> None:
        """Initialize the AddToModule customization.

        :param module_name: The name of the module to be added.
        :param property_name: The name of the property to be added to the module.
        :param value: The value of the property to be added to the module.
        :param exists_ok: Whether to ignore if the module already exists.
        """
        super().__init__(module_name)
        self.property_name = property_name
        self.value = value
        self.exists_ok = exists_ok

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        ret = builder.get_module(self.name)
        if hasattr(ret, self.property_name) and not self.exists_ok:
            raise ValueError(
                f"Property '{self.property_name}' already exists in module '{self.name}'."
            )
        setattr(ret, self.property_name, self.value)
