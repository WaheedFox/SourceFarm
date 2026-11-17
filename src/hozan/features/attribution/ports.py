"""Interfaces owned by the attribution core (no implementations here).

``EntitlementPort`` hides everything CUPS-specific (plan names, unified versus
single subscriptions, codes, partners). The policy only ever sees
``EntitlementStatus``. The adapter that talks to CUPS does not exist yet and is
out of scope for this part.
"""

from __future__ import annotations

from typing import Protocol

from .models import EntitlementStatus


class EntitlementPort(Protocol):
    async def get_status(self, *, owner_ref: str, product: str) -> EntitlementStatus:
        """Entitlement of ``owner_ref`` for ``product`` (a plain string key)."""
        ...
