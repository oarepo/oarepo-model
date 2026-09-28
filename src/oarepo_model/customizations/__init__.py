# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Customizations: change what oarepo-model generates without copying the generated code.

Pass them to ``model()`` in the ``customizations`` argument; they are applied after
the presets:

```python
from oarepo_model.api import model
from oarepo_model.customizations import (
    AddServiceComponent,
    SetPermissionPolicy,
)

equipment_model = model(
    "equipment",
    # ... presets, types, metadata_type etc.
    customizations=[
        AddServiceComponent(
            EquipmentComponent
        ),
        SetPermissionPolicy(
            EquipmentPermissionPolicy
        ),
    ],
)
```

There are two kinds:

- **High-level** customizations (``SetPermissionPolicy``, ``AddServiceComponent``,
  ``AddFacetGroup``, ``SetDefaultSearchFields``, ``PatchIndexMapping``,
  ``SetSyntheticMetadata``, ``AddMetadataExport``, ...) cover the common needs.
  Prefer them.
- **Low-level** customizations (``AddClass``, ``PrependMixin``, ``AddToList``,
  ``AddToDictionary``, ``PatchJSONFile``, ...) work on the named building blocks of
  the model (e.g. the ``Record`` class or the ``record_service_components`` list).
  The names are defined by the presets and may change between versions.

Everything can be imported from this package, except ``AddLink``, which lives in
``oarepo_model.customizations.high_level``.

See https://nrp-cz.github.io/docs/customize/model_backend/customizations
"""

from __future__ import annotations

from .add_base_class import AddBaseClass
from .add_class import AddClass
from .add_class_field import AddClassField
from .add_class_list import AddClassList
from .add_dictionary import AddDictionary
from .add_entry_point import AddEntryPoint
from .add_facet_group import AddFacetGroup
from .add_file_to_module import AddFileToModule
from .add_json_file import AddJSONFile
from .add_list import AddList
from .add_module import AddModule
from .add_to_dictionary import AddToDictionary
from .add_to_list import AddToList
from .add_to_module import AddToModule
from .base import Customization
from .change_base import ReplaceBaseClass
from .copy_file import CopyFile
from .high_level import (
    AddMetadataExport,
    AddMetadataImport,
    AddParamInterpreterCls,
    AddPIDRelation,
    AddServiceComponent,
    PatchIndexMapping,
    PatchIndexPropertyMapping,
    PatchIndexSettings,
    SetDefaultSearchFields,
    SetIndexNestedFieldsLimit,
    SetIndexTotalFieldsLimit,
    SetPermissionPolicy,
    SetSyntheticMetadata,
)
from .patch_json_file import PatchJSONFile
from .prepend_mixin import PrependMixin

__all__ = [
    "AddBaseClass",
    "AddClass",
    "AddClassField",
    "AddClassList",
    "AddDictionary",
    "AddEntryPoint",
    "AddFacetGroup",
    "AddFileToModule",
    "AddJSONFile",
    "AddList",
    "AddMetadataExport",
    "AddMetadataImport",
    "AddModule",
    "AddPIDRelation",
    "AddParamInterpreterCls",
    "AddServiceComponent",
    "AddToDictionary",
    "AddToList",
    "AddToModule",
    "CopyFile",
    "Customization",
    "PatchIndexMapping",
    "PatchIndexPropertyMapping",
    "PatchIndexSettings",
    "PatchJSONFile",
    "PrependMixin",
    "ReplaceBaseClass",
    "SetDefaultSearchFields",
    "SetIndexNestedFieldsLimit",
    "SetIndexTotalFieldsLimit",
    "SetPermissionPolicy",
    "SetSyntheticMetadata",
]
