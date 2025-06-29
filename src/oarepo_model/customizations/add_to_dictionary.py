from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddToDictionary(Customization):
    """Customization to add a value to a dictionary to the model."""

    def __init__(
        self, dictionary_name: str, key: str, value: Any, exists_ok: bool = False
    ) -> None:
        """Initialize the AddDictionary customization.

        :param name: The name of the dictionary to be added.
        :param default: The default value of the dictionary.
        :param exists_ok: Whether to ignore if the dictionary already exists.
        """
        super().__init__(dictionary_name)
        self.key = key
        self.value = value
        self.exists_ok = exists_ok

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        d = builder.add_dictionary(self.name, exists_ok=True)
        if self.key in d and not self.exists_ok:
            raise ValueError(
                f"Key '{self.key}' already exists in dictionary '{self.name}'."
            )
        d[self.key] = self.value
