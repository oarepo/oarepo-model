from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.customizations import Customization
    from oarepo_model.model import InvenioModel


class Preset:
    """
    Base class for presets.
    """

    provides: list[str] = []
    depends_on: list[str] = []

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        build_dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        """
        Apply the preset to the given model.
        This method should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")
