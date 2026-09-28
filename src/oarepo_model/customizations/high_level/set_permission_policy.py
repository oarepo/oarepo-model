# SPDX-FileCopyrightText: 2025-2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Permission policy: ``SetPermissionPolicy``.

Makes ``permission_policy`` (a subclass of
``invenio_records_permissions.policies.records.RecordPermissionPolicy``) the base
class of the model's ``PermissionPolicy``, used by the record and file services.
Mixins that presets added to ``PermissionPolicy`` are removed, so the policy
applies exactly as written; pass ``keep_mixins=True`` to keep them.

Without it (and without workflows), the model uses ``EveryonePermissionPolicy``,
which allows every action to anyone - suitable for development only.

Example (in ``model.py``):

```python
from invenio_records_permissions.generators import (
    AnyUser,
    AuthenticatedUser,
    SystemProcess,
)
from invenio_records_permissions.policies.records import (
    RecordPermissionPolicy,
)
from oarepo_model.customizations import (
    SetPermissionPolicy,
)


class EquipmentPermissionPolicy(
    RecordPermissionPolicy
):
    can_search = [
        SystemProcess(),
        AnyUser(),
    ]
    can_read = [
        SystemProcess(),
        AnyUser(),
    ]
    can_create = [
        SystemProcess(),
        AuthenticatedUser(),
    ]


SetPermissionPolicy(
    EquipmentPermissionPolicy
)
```

Include ``SystemProcess()`` in every action, otherwise background tasks and
command-line tools are denied as well.

See https://nrp-cz.github.io/docs/customize/model_backend/permissions
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ..base import Customization

if TYPE_CHECKING:
    from invenio_records_permissions.policies.records import RecordPermissionPolicy

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class SetPermissionPolicy(Customization):
    """Customization to set model's permission policy."""

    modifies = ("PermissionPolicy",)

    def __init__(self, permission_policy: type[RecordPermissionPolicy], keep_mixins: bool = False):
        """Initialize the SetPermissionPolicy customization."""
        super().__init__(permission_policy.__name__)
        self._permission_policy = permission_policy
        self._keep_mixins = keep_mixins

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        policy = builder.get_class("PermissionPolicy")
        policy.set_base_classes(self._permission_policy)
        if not self._keep_mixins:
            policy.set_mixins()
