# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from oarepo_model.api import model
from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.errors import PresetDeclarationWarning
from oarepo_model.presets.base import Preset
from oarepo_model.sorter import check_preset_declarations, sort_presets

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from oarepo_model.customizations import Customization
    from oarepo_model.model import InvenioModel

FIXED_IN_FUTURE = "will be treated as an error in a future version"


class CreatesPartial(Preset):
    """Preset that creates a partial."""

    def __init__(self, name: str, provides: tuple[str, ...] = ()) -> None:
        """Initialize the preset."""
        super().__init__()
        self.name = name
        self.provides = provides

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, object],
    ) -> Generator[Customization]:
        """Create the partial."""
        builder.add_dictionary(self.name)
        yield from ()


class UsesPartial(Preset):
    """Preset that writes into an existing partial."""

    def __init__(self, name: str, modifies: tuple[str, ...] = ()) -> None:
        """Initialize the preset."""
        super().__init__()
        self.name = name
        self.modifies = modifies

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, object],
    ) -> Generator[Customization]:
        """Write into the partial."""
        builder.get_dictionary(self.name)["key"] = "value"
        yield from ()


def _apply(presets: Sequence[Preset]) -> tuple[dict[str, Preset], dict[str, set[Preset]]]:
    builder = InvenioModelBuilder(MagicMock(), MagicMock())
    for preset in presets:
        builder.start_preset(preset)
        try:
            for customization in preset.apply(builder, MagicMock(), {}):
                customization.apply(builder, MagicMock())
        finally:
            builder.finish_preset()
    return builder.created_by, builder.touched_by


def _no_declaration_warning(presets: list[Preset]) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", PresetDeclarationWarning)
        check_preset_declarations(presets, *_apply(presets))


def test_partial_that_no_preset_provides_is_reported() -> None:
    presets = [CreatesPartial("Orphan")]

    with pytest.warns(PresetDeclarationWarning) as records:
        check_preset_declarations(presets, *_apply(presets))

    (message,) = [str(record.message) for record in records]
    assert "creates partial 'Orphan', but no preset provides it" in message
    assert FIXED_IN_FUTURE in message


def test_use_without_modifies_is_reported() -> None:
    presets = [CreatesPartial("Owned", provides=("Owned",)), UsesPartial("Owned")]

    with pytest.warns(PresetDeclarationWarning) as records:
        check_preset_declarations(presets, *_apply(presets))

    (message,) = [str(record.message) for record in records]
    assert "uses partial 'Owned', but does not declare it in modifies" in message
    assert FIXED_IN_FUTURE in message


class DependsOnlyOnPartial(Preset):
    """Preset that reads the final value of a partial it also writes into.

    This is the only way to express that: depends_on orders the preset after every declared
    modifier, while adding modifies too would make it depend on itself in the sorter.
    """

    depends_on = ("Owned",)

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, object],
    ) -> Generator[Customization]:
        """Write into the partial."""
        builder.get_dictionary("Owned")["key"] = "value"
        yield from ()


def test_depends_on_counts_as_a_declaration() -> None:
    _no_declaration_warning([CreatesPartial("Owned", provides=("Owned",)), DependsOnlyOnPartial()])


def test_modifier_is_sorted_after_provider_regardless_of_list_order() -> None:
    class Provider(Preset):
        provides = ("Owned",)

        def apply(self, builder, model, dependencies):
            yield from ()

    class Modifier(Preset):
        modifies = ("Owned",)

        def apply(self, builder, model, dependencies):
            yield from ()

    assert [type(p).__name__ for p in sort_presets([Modifier(), Provider()])] == [
        "Provider",
        "Modifier",
    ]


def test_declared_provides_and_modifies_are_not_reported() -> None:
    _no_declaration_warning([CreatesPartial("Owned", provides=("Owned",)), UsesPartial("Owned", modifies=("Owned",))])


def test_conditional_modification_is_not_reported() -> None:
    """A preset declaring more than this particular model happens to use is normal, not a bug."""

    class NeverModifies(Preset):
        modifies = ("NeverUsed",)

        def apply(
            self,
            builder: InvenioModelBuilder,
            model: InvenioModel,
            dependencies: dict[str, object],
        ) -> Generator[Customization]:
            yield from ()

    _no_declaration_warning([NeverModifies()])


def test_framework_presets_declare_everything_they_use() -> None:
    from oarepo_model.presets.drafts import drafts_preset
    from oarepo_model.presets.records_resources import records_resources_preset

    with warnings.catch_warnings():
        warnings.simplefilter("error", PresetDeclarationWarning)
        model(
            name="declaration_check_model",
            presets=[records_resources_preset, drafts_preset],
            version="1.0.0",
            types=[],
        )
