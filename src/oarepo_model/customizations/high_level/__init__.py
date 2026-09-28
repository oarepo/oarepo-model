# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""High-level customizations: the common changes to a model, without knowing its internals.

Pass them to ``model(customizations=[...])``:

- permissions - ``SetPermissionPolicy``
- service - ``AddServiceComponent``, ``AddLink``
- metadata - ``SetSyntheticMetadata``
- exports and imports - ``AddMetadataExport``, ``AddMetadataImport``
- search - ``SetDefaultSearchFields``, ``PatchIndexSettings``,
  ``SetIndexTotalFieldsLimit``, ``SetIndexNestedFieldsLimit``, ``PatchIndexMapping``,
  ``PatchIndexPropertyMapping``, ``AddFacetGroup``, ``AddParamInterpreterCls``

``AddPIDRelation``, ``AddLazyRelation`` and ``AddInternalRelation`` are generated from
the relation data types in the metadata; you rarely need them directly.

All of them can also be imported from ``oarepo_model.customizations``, except
``AddLink``, which is only available here.

See https://nrp-cz.github.io/docs/customize/model_backend/customizations#high-level-customizations-
"""

from __future__ import annotations

from .add_export import AddMetadataExport
from .add_import import AddMetadataImport
from .add_link import AddLink
from .add_param_interpreter_cls import AddParamInterpreterCls
from .add_pid_relation import AddPIDRelation
from .add_search_fields import SetDefaultSearchFields
from .add_service_component import AddServiceComponent
from .index_mapping import PatchIndexMapping, PatchIndexPropertyMapping
from .index_settings import (
    PatchIndexSettings,
    SetIndexNestedFieldsLimit,
    SetIndexTotalFieldsLimit,
)
from .set_permission_policy import SetPermissionPolicy
from .set_synthetic_metadata import SetSyntheticMetadata

__all__ = (
    "AddLink",
    "AddMetadataExport",
    "AddMetadataImport",
    "AddPIDRelation",
    "AddParamInterpreterCls",
    "AddServiceComponent",
    "PatchIndexMapping",
    "PatchIndexPropertyMapping",
    "PatchIndexSettings",
    "SetDefaultSearchFields",
    "SetIndexNestedFieldsLimit",
    "SetIndexTotalFieldsLimit",
    "SetPermissionPolicy",
    "SetSyntheticMetadata",
)
