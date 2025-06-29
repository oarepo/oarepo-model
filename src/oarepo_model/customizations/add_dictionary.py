from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddDictionary(Customization):
    """Customization to add a dictionary to the model.

    A dictionary is a collection of key-value pairs that will be added to the model.
    """

    def __init__(
        self, name: str, default: dict[str, Any] | None = None, exists_ok: bool = False
    ) -> None:
        """Initialize the AddDictionary customization.

        :param name: The name of the dictionary to be added.
        :param default: The default value of the dictionary.
        :param exists_ok: Whether to ignore if the dictionary already exists.
        """
        super().__init__(name)
        self.default = default
        self.exists_ok = exists_ok

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        builder.add_dictionary(self.name, self.default, exists_ok=self.exists_ok)
