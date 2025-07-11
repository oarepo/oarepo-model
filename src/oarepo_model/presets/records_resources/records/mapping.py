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


class MappingPreset(Preset):
    """
    Preset for records_resources.records.mapping
    """

    provides = ["mappings"]

    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization, None, None]:
        # TODO: this is a hack, need to fix invenio-jsonschemas to use importlib.resources
        # instead of direct file system access

        mappings_dir = str(Path(tempfile.mkdtemp() + "/mappings").resolve())

        def cleanup(dirname):
            """Cleanup function to remove the mappings directory."""
            if Path(dirname).exists():
                shutil.rmtree(dirname)

        atexit.register(cleanup, mappings_dir)
        yield AddModule("mappings", file_path=mappings_dir, exists_ok=True)

        yield AddEntryPoint(
            group="invenio_search.mappings",
            name=model.base_name,
            separator=".",
            value="mappings",
        )
