from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddFileToModule(Customization):
    """Customization to add a property to a module to the model."""

    def __init__(
        self,
        module_name: str,
        file_path: str,
        file_content: str | bytes,
        exists_ok: bool = False,
    ) -> None:
        """Initialize the AddFileToModule customization.

        :param module_name: The name of the module to be added.
        :param file_path: The path to the file to be added to the module.
        :param file_content: The content of the file to be added to the module.
        :param exists_ok: Whether to ignore if the module already exists.
        """
        super().__init__(module_name)
        self.file_path = file_path
        self.file_content = file_content
        self.exists_ok = exists_ok

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        # note: implementation should be changed to be in-memory only
        # (with cooperation of oarepo_model.register)
        ret = builder.get_module(self.name)
        base_directory = ret.__file__
        if not base_directory.endswith("/__init__.py"):
            raise ValueError(f"Module '{self.name}' does not have a valid file path.")
        pth = Path(base_directory).parent / self.file_path
        pth.parent.mkdir(parents=True, exist_ok=True)
        if pth.exists() and not self.exists_ok:
            raise ValueError(
                f"File '{self.file_path}' already exists in module '{self.name}'."
            )
        with pth.open("wb") as f:
            if isinstance(self.file_content, str):
                f.write(self.file_content.encode("utf-8"))
            else:
                f.write(self.file_content)
