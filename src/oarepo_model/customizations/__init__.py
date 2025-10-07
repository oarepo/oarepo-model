#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Customization classes for OARepo model building.

This module provides various customization classes that can be used to modify
and extend OARepo models during the building process. These customizations
allow adding classes, modifying configurations, and extending model functionality.
"""

from __future__ import annotations

from .add_base_class import AddBaseClasses
from .add_class import AddClass
from .add_class_field import AddClassField
from .add_class_list import AddClassList
from .add_dictionary import AddDictionary
from .add_entry_point import AddEntryPoint
from .add_facet_group import AddFacetGroup
from .add_file_to_module import AddFileToModule
from .add_json_file import AddJSONFile
from .add_list import AddList
from .add_mixin import AddMixins
from .add_module import AddModule
from .add_to_dictionary import AddToDictionary
from .add_to_list import AddToList
from .add_to_module import AddToModule
from .base import Customization
from .change_base import ChangeBase
from .copy_file import CopyFile
from .high_level import (
    AddDefaultSearchFields,
    AddMetadataExport,
    AddPIDRelation,
    IndexNestedFieldsLimit,
    IndexSettings,
    IndexTotalFieldsLimit,
    SetPermissionPolicy,
)
from .patch_json_file import PatchJSONFile

__all__ = [
    "AddBaseClasses",
    "AddClass",
    "AddClassField",
    "AddClassList",
    "AddDefaultSearchFields",
    "AddDictionary",
    "AddEntryPoint",
    "AddFacetGroup",
    "AddFileToModule",
    "AddJSONFile",
    "AddList",
    "AddMetadataExport",
    "AddMixins",
    "AddModule",
    "AddPIDRelation",
    "AddToDictionary",
    "AddToList",
    "AddToModule",
    "ChangeBase",
    "CopyFile",
    "Customization",
    "IndexNestedFieldsLimit",
    "IndexSettings",
    "IndexTotalFieldsLimit",
    "PatchJSONFile",
    "SetPermissionPolicy",
]
