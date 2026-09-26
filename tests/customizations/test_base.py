# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from oarepo_model.customizations import AddEntryPoint
from oarepo_model.customizations.high_level.add_internal_relation import AddInternalRelation
from oarepo_model.customizations.high_level.add_pid_relation import AddPIDRelation

if TYPE_CHECKING:
    from invenio_records_resources.records.systemfields.pid import PIDFieldContext


def test_customization_repr_contains_class_and_name():
    assert repr(AddEntryPoint("invenio_base.api_blueprints", "records", "records_blueprint")) == (
        "<Customization AddEntryPoint 'records'>"
    )


def test_relation_customization_name_is_the_relation_name():
    # the name given to super().__init__ must be the relation name, not a placeholder
    pid_relation = AddPIDRelation("affiliations", ["affiliations"], ["id"], pid_field=cast("PIDFieldContext", None))
    assert repr(pid_relation) == "<Customization AddPIDRelation 'affiliations'>"

    internal_relation = AddInternalRelation("polymers", ["polymers"], ["polymer_id"], "polymers")
    assert repr(internal_relation) == "<Customization AddInternalRelation 'polymers'>"
