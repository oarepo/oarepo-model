#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from .add_base_class import AddBaseClasses
from .add_class import AddClass
from .add_class_field import AddClassField
from .add_class_list import AddClassList
from .add_dictionary import AddDictionary
from .add_entry_point import AddEntryPoint
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
from .high_level import AddPIDRelation
from .patch_json_file import PatchJSONFile

__all__ = [
    "Customization",
    "AddBaseClasses",
    "AddClass",
    "AddClassField",
    "AddClassList",
    "AddDictionary",
    "AddEntryPoint",
    "AddFileToModule",
    "AddJSONFile",
    "AddList",
    "AddMixins",
    "AddModule",
    "AddToDictionary",
    "AddToList",
    "AddToModule",
    "ChangeBase",
    "CopyFile",
    "PatchJSONFile",
    "AddPIDRelation",
]
