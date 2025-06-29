#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import atexit
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator

from oarepo_model.customizations import AddEntryPoint, AddModule, Customization
from oarepo_model.model import InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder


class JSONSchemaPreset(Preset):
    """
    Preset for records_resources.records.jsonschema
    """

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        # TODO: this is a hack, need to fix invenio-jsonschemas to use importlib.resources
        # instead of direct file system access

        jsonschemas_dir = str(Path(tempfile.mkdtemp() + "/jsonschemas").resolve())
        atexit.register(shutil.rmtree, jsonschemas_dir)
        yield AddModule("jsonschemas", file_path=jsonschemas_dir, exists_ok=True)

        yield AddEntryPoint(
            group="invenio_jsonschemas.schemas",
            name=model.base_name,
            separator=".",
            value="jsonschemas",
        )
