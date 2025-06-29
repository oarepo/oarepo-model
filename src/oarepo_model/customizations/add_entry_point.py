from __future__ import annotations

from typing import TYPE_CHECKING, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddEntryPoint(Customization):
    """Customization to add an entry point to the model.

    An entry point is a specific location in the code where a certain functionality can be accessed.
    """

    def __init__(
        self,
        group: str,
        name: str,
        value: str,
        separator: str = ":",
        overwrite: bool = False,
    ) -> None:
        """Initialize the AddEntryPoint customization.

        :param group: The group to which the entry point belongs.
        :param name: The name of the entry point.
        :param separator: The separator to use in the entry point.
        :param value: The value of the entry point.
        """
        super().__init__(f"{group}::{name}::{value}")
        self.group = group
        self.name = name
        self.separator = separator
        self.value = value
        self.overwrite = overwrite

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        builder.add_entry_point(
            group=self.group,
            name=self.name,
            separator=self.separator,
            value=self.value,
            overwrite=self.overwrite,
        )
