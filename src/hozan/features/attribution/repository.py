"""Signature state for groups and channels: claim, confirm, release.

Private chats have no state and never use this repository.

Claim lifecycle (the contract every implementation must honour)
---------------------------------------------------------------
``try_claim`` creates an exclusive, time-limited claim on a ``SignatureTarget``.
It succeeds only if BOTH hold at the moment of the call:

* the window is open (``evaluate_window``: no previous signature, or at least
  ``window`` has elapsed since the previous signature was CONFIRMED), and
* there is no unexpired claim held by someone else.

A claim created at ``now`` with ``claim_ttl`` is valid for ``[now, now + claim_ttl)``.
At ``now' >= now + claim_ttl`` it is expired.

Outcomes of ``try_claim`` (``ClaimStatus``):

* ``CLAIMED``                  exclusive claim granted; carries an opaque token.
* ``WINDOW_ACTIVE``           a signature was confirmed less than ``window`` ago.
* ``CLAIM_PENDING``           another unexpired claim exists. This is what prevents
                              two conflicting claims: while a claim is unexpired
                              nobody else can obtain one.
* ``LAST_SIGNATURE_IN_FUTURE`` the stored last-signature time is later than ``now``.
                              Explicit, never treated as "open". A warning is logged
                              and NO state is changed.

What happens when the TTL runs out while the holder is still working
--------------------------------------------------------------------
* While the claim is unexpired: other callers get ``CLAIM_PENDING``.
* Once it has expired, the next ``try_claim`` SUPERSEDES it with a new claim and a
  new token. From then on the old token is STALE:
    - ``confirm(old_token)`` returns ``False`` and changes nothing,
    - ``release(old_token)`` returns ``False`` and changes nothing (it can never
      clear the new holder's claim).
  If the old holder had in fact already sent its signature, two signatures can
  exist. This is an unavoidable race when the TTL is shorter than the real send
  duration; callers should choose ``claim_ttl`` longer than their longest send
  timeout. This contract does not remove that duplicate risk, it only makes it
  explicit and keeps the stored state consistent.
* If the claim expired but has NOT been superseded, its token is still accepted by
  ``confirm`` and ``release``: the signature was already sent, so recording it is
  better than losing it.

``confirm(token, confirmed_at)``
    Records that the signature was really sent. ``last_signature_at`` becomes
    ``confirmed_at``: the window is measured from CONFIRMATION, never from the
    claim or from the send attempt. Returns ``False`` (no change) if the token is
    not the current claim. Raises ``ValueError`` (no change) if ``confirmed_at`` is
    earlier than the claim's creation time.

``release(token)``
    Drops the claim WITHOUT touching ``last_signature_at``: a failed attempt does
    not consume the window. Returns ``False`` (no change) if the token is not the
    current claim.

What this contract does NOT cover
---------------------------------
* How an ambiguous send outcome (timeout, lost response) is classified. That is an
  open decision (D11); the caller chooses ``confirm`` or ``release``.
* Durable storage. See ``memory.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Protocol

from .models import SignatureTarget


class ClaimStatus(str, Enum):
    CLAIMED = "claimed"
    WINDOW_ACTIVE = "window_active"
    CLAIM_PENDING = "claim_pending"
    LAST_SIGNATURE_IN_FUTURE = "last_signature_in_future"


@dataclass(frozen=True, slots=True)
class ClaimResult:
    status: ClaimStatus
    token: str | None = None
    expires_at: datetime | None = None

    @property
    def claimed(self) -> bool:
        return self.status is ClaimStatus.CLAIMED


class SignatureStateRepository(Protocol):
    async def get_last_signature_at(self, target: SignatureTarget) -> datetime | None:
        ...

    async def try_claim(
        self,
        target: SignatureTarget,
        *,
        now: datetime,
        window: timedelta,
        claim_ttl: timedelta,
    ) -> ClaimResult:
        ...

    async def confirm(
        self,
        target: SignatureTarget,
        token: str,
        *,
        confirmed_at: datetime,
    ) -> bool:
        ...

    async def release(self, target: SignatureTarget, token: str) -> bool:
        ...
