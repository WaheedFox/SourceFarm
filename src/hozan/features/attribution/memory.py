"""In-memory ``SignatureStateRepository``: a TEMPORARY implementation for tests.

This is NOT production storage and NOT evidence that durable storage or
concurrency is correct. Its atomicity comes only from running on a single asyncio
event loop with no ``await`` inside any critical section. A real store needs
transactions or compare-and-set, a database clock, and its own tests.
"""

from __future__ import annotations

import logging
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import (
    SignatureTarget,
    WindowState,
    ensure_positive_timedelta,
    ensure_utc,
    evaluate_window,
)
from .repository import ClaimResult, ClaimStatus

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _Claim:
    token: str
    claimed_at: datetime
    expires_at: datetime


@dataclass(slots=True)
class _Record:
    last_signature_at: datetime | None = None
    claim: _Claim | None = None


def _default_token() -> str:
    return secrets.token_hex(16)


def _check_target(target: object) -> SignatureTarget:
    if not isinstance(target, SignatureTarget):
        raise TypeError("target must be a SignatureTarget")
    return target


def _check_token(token: object) -> str:
    if not isinstance(token, str) or not token:
        raise TypeError("token must be a non-empty str")
    return token


class MemorySignatureStateRepository:
    def __init__(self, *, token_factory: Callable[[], str] | None = None) -> None:
        self._records: dict[SignatureTarget, _Record] = {}
        self._token_factory = token_factory or _default_token

    async def get_last_signature_at(self, target: SignatureTarget) -> datetime | None:
        record = self._records.get(_check_target(target))
        return record.last_signature_at if record else None

    async def try_claim(
        self,
        target: SignatureTarget,
        *,
        now: datetime,
        window: timedelta,
        claim_ttl: timedelta,
    ) -> ClaimResult:
        _check_target(target)
        ensure_utc(now, "now")
        ensure_positive_timedelta(window, "window")
        ensure_positive_timedelta(claim_ttl, "claim_ttl")

        record = self._records.get(target)
        last = record.last_signature_at if record else None
        state = evaluate_window(last_signature_at=last, now=now, window=window)

        if state is WindowState.FUTURE:
            logger.warning(
                "claim refused: last_signature_at is in the future "
                "(now=%s, last_signature_at=%s); state is not modified",
                now.isoformat(),
                last.isoformat() if last else None,
            )
            return ClaimResult(ClaimStatus.LAST_SIGNATURE_IN_FUTURE)
        if state is WindowState.ACTIVE:
            return ClaimResult(ClaimStatus.WINDOW_ACTIVE)

        if record is not None and record.claim is not None:
            if now < record.claim.expires_at:
                return ClaimResult(ClaimStatus.CLAIM_PENDING)
            # expired: superseded below; the old token becomes stale.

        if record is None:
            record = self._records[target] = _Record()
        token = self._token_factory()
        expires_at = now + claim_ttl
        record.claim = _Claim(token=token, claimed_at=now, expires_at=expires_at)
        return ClaimResult(ClaimStatus.CLAIMED, token=token, expires_at=expires_at)

    async def confirm(
        self,
        target: SignatureTarget,
        token: str,
        *,
        confirmed_at: datetime,
    ) -> bool:
        _check_target(target)
        _check_token(token)
        ensure_utc(confirmed_at, "confirmed_at")

        record = self._records.get(target)
        if record is None or record.claim is None or record.claim.token != token:
            return False
        if confirmed_at < record.claim.claimed_at:
            raise ValueError("confirmed_at is earlier than the time of the claim")
        record.last_signature_at = confirmed_at
        record.claim = None
        return True

    async def release(self, target: SignatureTarget, token: str) -> bool:
        _check_target(target)
        _check_token(token)
        record = self._records.get(target)
        if record is None or record.claim is None or record.claim.token != token:
            return False
        record.claim = None
        return True
