from __future__ import annotations

from typing import TYPE_CHECKING, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddModule(Customization):
    """Customization to add a module to the model.

    A module is a collection of related classes and functions that are organized together.
    """

    def __init__(
        self,
        name: str,
        exists_ok: bool = False,
        file_path: str | None = None,
    ) -> None:
        """Initialize the AddModule customization.

        :param name: The name of the module to be added.
        :param exists_ok: Whether to ignore if the module already exists.
        """
        super().__init__(name)
        self.exists_ok = exists_ok
        self.file_path = file_path

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        ret = builder.add_module(self.name, exists_ok=self.exists_ok)
        if self.file_path:
            # always a package so that we can add files to it
            ret.__file__ = self.file_path + "/" + "__init__.py"
