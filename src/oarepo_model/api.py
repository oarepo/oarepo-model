from functools import cmp_to_key, partial
from types import SimpleNamespace
from typing import Any

from .builder import InvenioModelBuilder
from .customizations import Customization
from .model import InvenioModel
from .presets import Preset
from .register import register_model


def model(
    name: str,
    presets: list[type[Preset] | list[type[Preset]] | tuple[type[Preset]]] = [],
    *,
    description: str = "",
    version: str = "0.1.0",
    configuration: dict[str, Any] | None = None,
    customizations: list[Customization] | None = None,
) -> SimpleNamespace:
    """
    Create a model with the given name, version, and presets.

    :param name: The name of the model.
    :param presets: A list of presets to apply to the model.
    :param description: A description of the model.
    :param version: The version of the model.
    :param config: Configuration for the model.
    :param customizations: Customizations for the model.
    :return: An instance of InvenioModel.
    """

    model = InvenioModel(
        name=name,
        version=version,
        description=description,
        configuration=configuration or {},
    )

    builder = InvenioModelBuilder(model)

    # get all presets
    sorted_presets: list[Preset] = []
    for preset_list_or_preset in presets:
        if not isinstance(preset_list_or_preset, (list, tuple)):
            preset_list_or_preset = [preset_list_or_preset]
        for preset_cls in preset_list_or_preset:
            preset = preset_cls()
            sorted_presets.append(preset)

    # reorder customizations to ensure dependencies are respected
    def reorder_cmp(a: Preset, b: Preset):
        # if a depends on b
        if any(bb in a.provides for bb in b.depends_on):
            # b depends on a, so a should come after a
            return -1
        if any(aa in b.provides for aa in a.depends_on):
            # a depends on b, so a should come before b
            return 1
        # otherwise, they are independent, so keep the original order
        return 0

    sorted_presets.sort(key=cmp_to_key(reorder_cmp))

    user_customizations = [*(customizations or [])]

    for preset in sorted_presets:
        # if preset depends on something, make sure user customizations
        # for that dependency are applied
        idx = 0
        while idx < len(user_customizations):
            customization = user_customizations[idx]
            if customization.name in preset.depends_on:
                customization.apply(builder, model)
                user_customizations.pop(idx)
            else:
                idx += 1
        build_dependencies = {
            dep: builder.build_partial(dep) for dep in preset.depends_on
        }
        for customization in preset.apply(builder, model, build_dependencies):
            customization.apply(builder, model)

    for customization in user_customizations:
        # apply user customizations that were not handled by presets
        customization.apply(builder, model)

    # maybe replace this with a LazyNamespace if there are dependency issues
    ret = builder.build()

    ret.register = partial(register_model, model=model, namespace=ret)
    return ret
