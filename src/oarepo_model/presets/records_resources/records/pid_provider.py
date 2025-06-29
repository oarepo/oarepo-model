from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from invenio_pidstore.providers.recordid_v2 import RecordIdProviderV2
from invenio_records_resources.records.systemfields.pid import PIDField, PIDFieldContext
from oarepo_runtime.records.pid_providers import UniversalPIDMixin

from oarepo_model.customizations import AddClass, AddMixins, Customization
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class PIDProviderPreset(Preset):
    """
    Preset for pid provider class
    """

    provides = [
        "PIDProvider",
        "PIDField",
        "PIDFieldContext",
    ]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        class PIDProviderMixin:
            pid_type = builder.model.configuration.get("pid_type") or make_pid_type(
                builder.model.base_name
            )

        yield AddClass("PIDProvider", clazz=RecordIdProviderV2)
        yield AddMixins("PIDProvider", UniversalPIDMixin, PIDProviderMixin)

        yield AddClass("PIDField", clazz=PIDField)
        yield AddClass("PIDFieldContext", clazz=PIDFieldContext)


def make_pid_type(base_name: str) -> str:
    """Generate a PID type based on the base name of the model.

    The PID type is maximum of 6 characters long and is derived from the base name
    of the model as:

    1. Convert the base name to lowercase.
    2. Remove all non alphabetic characters.
    3. If too long, start removing vowels from the end until it fits.
    4. if still too long, remove middle characters until it fits.
    """
    pid_type = base_name.lower()
    pid_type = "".join(c for c in pid_type if c.isalpha())
    if len(pid_type) < 6:
        return pid_type

    # Remove vowels from the end
    vowels = "aeiou"
    while len(pid_type) > 6:
        for i in range(len(pid_type) - 1, -1, -1):
            if pid_type[i] in vowels:
                pid_type = pid_type[:i] + pid_type[i + 1 :]
                break
        else:
            # No vowels found, break the loop
            break

    if len(pid_type) <= 6:
        return pid_type

    # If still too long, remove characters from the middle
    while len(pid_type) > 6:
        mid_index = len(pid_type) // 2
        pid_type = pid_type[:mid_index] + pid_type[mid_index + 1 :]

    return pid_type
