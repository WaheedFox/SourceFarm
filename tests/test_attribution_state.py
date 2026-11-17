"""Tests for the claim / confirm / release contract.

They run against ``MemorySignatureStateRepository``, a TEMPORARY test
implementation. Passing them demonstrates the CONTRACT described in
``repository.py``; it does not prove that any durable store or any real
concurrency is correct.

Scenario mapping (see also test_attribution_policy.py)
------------------------------------------------------
T06 first group/channel batch can claim                -> CLAIMED
T07 batch inside 24h cannot claim                      -> WINDOW_ACTIVE (after a confirmed signature)
T08 first batch after 24h can claim                    -> CLAIMED (boundary ">=")
T09 channels behave exactly like groups                -> same state logic (the state is keyed by chat id only)
T10 two bots (projects) in the same chat               -> independent state
T11 a failed attempt does not consume the window       -> release keeps the window open
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest

from hozan.features.attribution import (
    SIGNATURE_WINDOW,
    ClaimStatus,
    MemorySignatureStateRepository,
    SignatureTarget,
)

T0 = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)
WINDOW = SIGNATURE_WINDOW
TTL = timedelta(seconds=30)
TARGET = SignatureTarget(project_id="p1", chat_id=-1001)


class _ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@contextmanager
def captured_warnings():
    logger = logging.getLogger("hozan.features.attribution")
    handler = _ListHandler()
    logger.addHandler(handler)
    try:
        yield handler.records
    finally:
        logger.removeHandler(handler)


def counting_tokens():
    counter = {"n": 0}

    def factory() -> str:
        counter["n"] += 1
        return f"tok-{counter['n']}"

    return factory


def new_repo() -> MemorySignatureStateRepository:
    return MemorySignatureStateRepository(token_factory=counting_tokens())


async def claim(repo, target=TARGET, *, now=T0, window=WINDOW, ttl=TTL):
    return await repo.try_claim(target, now=now, window=window, claim_ttl=ttl)


# --------------------------------------------------------------------------
# Basic lifecycle (T06, T07, T08, T09, T11)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_t06_first_claim_on_an_empty_state_succeeds():
    repo = new_repo()
    result = await claim(repo)
    assert result.status is ClaimStatus.CLAIMED
    assert result.claimed
    assert result.token == "tok-1"
    assert result.expires_at == T0 + TTL
    assert await repo.get_last_signature_at(TARGET) is None


@pytest.mark.asyncio
async def test_claim_alone_does_not_start_the_window():
    repo = new_repo()
    await claim(repo)
    assert await repo.get_last_signature_at(TARGET) is None


@pytest.mark.asyncio
async def test_t07_window_is_active_after_a_confirmed_signature():
    repo = new_repo()
    first = await claim(repo)
    assert await repo.confirm(TARGET, first.token, confirmed_at=T0 + timedelta(seconds=5))
    later = await claim(repo, now=T0 + timedelta(hours=1))
    assert later.status is ClaimStatus.WINDOW_ACTIVE
    assert later.token is None


@pytest.mark.asyncio
async def test_window_is_measured_from_confirmation_not_from_claim_or_attempt():
    repo = new_repo()
    claimed_at = T0
    confirmed_at = T0 + timedelta(minutes=10)
    first = await claim(repo, now=claimed_at, ttl=timedelta(minutes=20))
    assert await repo.confirm(TARGET, first.token, confirmed_at=confirmed_at)
    assert await repo.get_last_signature_at(TARGET) == confirmed_at

    # 24h after the CLAIM but still inside 24h after the CONFIRMATION: closed.
    probe_a = await claim(repo, now=claimed_at + WINDOW)
    assert probe_a.status is ClaimStatus.WINDOW_ACTIVE
    # One microsecond before 24h after confirmation: still closed.
    probe_b = await claim(repo, now=confirmed_at + WINDOW - timedelta(microseconds=1))
    assert probe_b.status is ClaimStatus.WINDOW_ACTIVE
    # Exactly 24h after confirmation: open (>=).
    probe_c = await claim(repo, now=confirmed_at + WINDOW)
    assert probe_c.status is ClaimStatus.CLAIMED


@pytest.mark.asyncio
@pytest.mark.parametrize("extra", [timedelta(0), timedelta(seconds=1), timedelta(days=3)])
async def test_t08_first_claim_after_the_window_succeeds(extra):
    repo = new_repo()
    first = await claim(repo)
    assert await repo.confirm(TARGET, first.token, confirmed_at=T0)
    again = await claim(repo, now=T0 + WINDOW + extra)
    assert again.status is ClaimStatus.CLAIMED


@pytest.mark.asyncio
async def test_t11_release_keeps_the_window_open_failure_does_not_consume_it():
    repo = new_repo()
    first = await claim(repo)
    assert await repo.release(TARGET, first.token)
    assert await repo.get_last_signature_at(TARGET) is None
    second = await claim(repo, now=T0 + timedelta(seconds=1))
    assert second.status is ClaimStatus.CLAIMED
    assert second.token != first.token


@pytest.mark.asyncio
async def test_release_never_changes_an_existing_last_signature_time():
    repo = new_repo()
    first = await claim(repo)
    await repo.confirm(TARGET, first.token, confirmed_at=T0)
    reopened = T0 + WINDOW
    second = await claim(repo, now=reopened)
    assert await repo.release(TARGET, second.token)
    assert await repo.get_last_signature_at(TARGET) == T0


# --------------------------------------------------------------------------
# Conflicting claims
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_second_claim_while_the_first_is_unexpired_is_pending():
    repo = new_repo()
    await claim(repo)
    other = await claim(repo, now=T0 + timedelta(seconds=10))
    assert other.status is ClaimStatus.CLAIM_PENDING
    assert other.token is None


@pytest.mark.asyncio
async def test_concurrent_claims_produce_exactly_one_winner():
    repo = new_repo()
    results = await asyncio.gather(*[claim(repo) for _ in range(25)])
    statuses = [r.status for r in results]
    assert statuses.count(ClaimStatus.CLAIMED) == 1
    assert statuses.count(ClaimStatus.CLAIM_PENDING) == 24


@pytest.mark.asyncio
async def test_claim_is_valid_up_to_but_excluding_its_expiry_instant():
    repo = new_repo()
    await claim(repo)  # valid on [T0, T0 + TTL)
    just_before = await claim(repo, now=T0 + TTL - timedelta(microseconds=1))
    assert just_before.status is ClaimStatus.CLAIM_PENDING
    at_expiry = await claim(repo, now=T0 + TTL)
    assert at_expiry.status is ClaimStatus.CLAIMED


# --------------------------------------------------------------------------
# TTL expiry while another operation proceeds
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_expired_claim_is_superseded_and_the_old_token_becomes_stale():
    repo = new_repo()
    old = await claim(repo)
    new = await claim(repo, now=T0 + TTL + timedelta(seconds=1))
    assert new.status is ClaimStatus.CLAIMED
    assert new.token != old.token

    # The stale holder can neither confirm nor release, and changes nothing.
    assert await repo.confirm(TARGET, old.token, confirmed_at=T0 + timedelta(minutes=2)) is False
    assert await repo.get_last_signature_at(TARGET) is None
    assert await repo.release(TARGET, old.token) is False

    # The new holder's claim is untouched by the stale attempts.
    pending = await claim(repo, now=T0 + TTL + timedelta(seconds=2))
    assert pending.status is ClaimStatus.CLAIM_PENDING
    assert await repo.confirm(TARGET, new.token, confirmed_at=T0 + timedelta(minutes=3))
    assert await repo.get_last_signature_at(TARGET) == T0 + timedelta(minutes=3)


@pytest.mark.asyncio
async def test_expired_but_not_superseded_claim_can_still_confirm():
    repo = new_repo()
    held = await claim(repo)
    late = T0 + TTL + timedelta(minutes=5)
    assert await repo.confirm(TARGET, held.token, confirmed_at=late) is True
    assert await repo.get_last_signature_at(TARGET) == late


@pytest.mark.asyncio
async def test_expired_but_not_superseded_claim_can_still_release():
    repo = new_repo()
    held = await claim(repo)
    assert await repo.release(TARGET, held.token) is True


@pytest.mark.asyncio
async def test_superseding_claim_keeps_the_window_rule():
    repo = new_repo()
    first = await claim(repo)
    await repo.confirm(TARGET, first.token, confirmed_at=T0)
    second = await claim(repo, now=T0 + WINDOW)
    assert second.claimed
    # second expires, a third supersedes it
    third = await claim(repo, now=T0 + WINDOW + TTL)
    assert third.claimed and third.token != second.token
    assert await repo.get_last_signature_at(TARGET) == T0


# --------------------------------------------------------------------------
# confirm / release edge cases
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_and_release_without_a_claim_return_false():
    repo = new_repo()
    assert await repo.confirm(TARGET, "x", confirmed_at=T0) is False
    assert await repo.release(TARGET, "x") is False
    assert await repo.get_last_signature_at(TARGET) is None


@pytest.mark.asyncio
async def test_confirm_with_a_wrong_token_changes_nothing():
    repo = new_repo()
    held = await claim(repo)
    assert await repo.confirm(TARGET, "wrong", confirmed_at=T0 + timedelta(seconds=1)) is False
    assert await repo.get_last_signature_at(TARGET) is None
    # the real holder can still confirm afterwards
    assert await repo.confirm(TARGET, held.token, confirmed_at=T0 + timedelta(seconds=2))


@pytest.mark.asyncio
async def test_confirm_twice_second_call_is_false():
    repo = new_repo()
    held = await claim(repo)
    assert await repo.confirm(TARGET, held.token, confirmed_at=T0 + timedelta(seconds=1))
    assert await repo.confirm(TARGET, held.token, confirmed_at=T0 + timedelta(seconds=2)) is False
    assert await repo.get_last_signature_at(TARGET) == T0 + timedelta(seconds=1)


@pytest.mark.asyncio
async def test_confirmed_at_earlier_than_the_claim_is_rejected_without_state_change():
    repo = new_repo()
    held = await claim(repo)
    with pytest.raises(ValueError, match="earlier"):
        await repo.confirm(TARGET, held.token, confirmed_at=T0 - timedelta(seconds=1))
    assert await repo.get_last_signature_at(TARGET) is None
    # the claim is still held and usable
    assert await repo.confirm(TARGET, held.token, confirmed_at=T0)


# --------------------------------------------------------------------------
# Future last_signature_at (state is kept, never modified, always logged)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_future_last_signature_refuses_the_claim_logs_and_changes_nothing():
    repo = new_repo()
    held = await claim(repo, now=T0 + timedelta(hours=2))
    future = T0 + timedelta(hours=2, seconds=1)
    assert await repo.confirm(TARGET, held.token, confirmed_at=future)

    with captured_warnings() as records:
        result = await claim(repo, now=T0)
    assert result.status is ClaimStatus.LAST_SIGNATURE_IN_FUTURE
    assert result.token is None
    assert len(records) == 1
    assert "future" in records[0].getMessage()
    # state untouched: same last signature, and no claim was created
    assert await repo.get_last_signature_at(TARGET) == future
    with captured_warnings() as records_again:
        again = await claim(repo, now=T0)
    assert again.status is ClaimStatus.LAST_SIGNATURE_IN_FUTURE  # not CLAIM_PENDING
    assert len(records_again) == 1


# --------------------------------------------------------------------------
# T10: independence per (project, chat)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_t10_two_projects_in_the_same_chat_are_independent():
    repo = new_repo()
    a = SignatureTarget("project-a", -1001)
    b = SignatureTarget("project-b", -1001)

    claim_a = await claim(repo, a)
    assert claim_a.claimed
    assert await repo.confirm(a, claim_a.token, confirmed_at=T0)

    # B is unaffected by A's confirmed signature and by A's earlier claim.
    claim_b = await claim(repo, b, now=T0 + timedelta(seconds=1))
    assert claim_b.status is ClaimStatus.CLAIMED
    assert await repo.get_last_signature_at(b) is None
    # A is still inside its window.
    assert (await claim(repo, a, now=T0 + timedelta(hours=1))).status is ClaimStatus.WINDOW_ACTIVE
    # B's pending claim does not block A's later window either way.
    assert (await claim(repo, b, now=T0 + timedelta(seconds=2))).status is ClaimStatus.CLAIM_PENDING


@pytest.mark.asyncio
async def test_same_project_in_two_chats_is_independent():
    repo = new_repo()
    chat1 = SignatureTarget("p", -1001)
    chat2 = SignatureTarget("p", -1002)
    first = await claim(repo, chat1)
    await repo.confirm(chat1, first.token, confirmed_at=T0)
    other = await claim(repo, chat2, now=T0 + timedelta(seconds=1))
    assert other.status is ClaimStatus.CLAIMED


@pytest.mark.asyncio
async def test_a_token_of_one_target_cannot_act_on_another_target():
    repo = new_repo()
    a = SignatureTarget("project-a", -1001)
    b = SignatureTarget("project-b", -1001)
    claim_a = await claim(repo, a)
    claim_b = await claim(repo, b)
    assert await repo.confirm(b, claim_a.token, confirmed_at=T0) is False
    assert await repo.release(b, claim_a.token) is False
    assert await repo.get_last_signature_at(a) is None
    assert await repo.get_last_signature_at(b) is None
    assert claim_b.claimed


# --------------------------------------------------------------------------
# Input validation: rejected, never converted
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_naive_now_is_rejected():
    repo = new_repo()
    with pytest.raises(ValueError, match="timezone-aware"):
        await claim(repo, now=datetime(2026, 11, 15, 12, 0))


@pytest.mark.asyncio
async def test_non_utc_now_is_rejected():
    repo = new_repo()
    with pytest.raises(ValueError, match="UTC"):
        await claim(repo, now=datetime(2026, 11, 15, 15, 0, tzinfo=timezone(timedelta(hours=3))))


@pytest.mark.asyncio
async def test_naive_confirmed_at_is_rejected():
    repo = new_repo()
    held = await claim(repo)
    with pytest.raises(ValueError, match="timezone-aware"):
        await repo.confirm(TARGET, held.token, confirmed_at=datetime(2026, 11, 15, 12, 0))


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", [timedelta(0), timedelta(seconds=-5)])
async def test_claim_ttl_must_be_positive(bad):
    repo = new_repo()
    with pytest.raises(ValueError):
        await claim(repo, ttl=bad)
    assert await repo.get_last_signature_at(TARGET) is None


@pytest.mark.asyncio
async def test_claim_ttl_is_required_and_must_be_a_timedelta():
    repo = new_repo()
    with pytest.raises(TypeError):
        await repo.try_claim(TARGET, now=T0, window=WINDOW)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        await claim(repo, ttl=30)  # type: ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", [timedelta(0), timedelta(hours=-1)])
async def test_window_must_be_positive(bad):
    repo = new_repo()
    with pytest.raises(ValueError):
        await claim(repo, window=bad)


@pytest.mark.asyncio
async def test_invalid_inputs_do_not_create_a_claim():
    repo = new_repo()
    with pytest.raises(ValueError):
        await claim(repo, ttl=timedelta(0))
    good = await claim(repo)
    assert good.claimed


def test_target_validation():
    with pytest.raises(ValueError):
        SignatureTarget("", 1)
    with pytest.raises(ValueError):
        SignatureTarget("   ", 1)
    with pytest.raises(TypeError):
        SignatureTarget(5, 1)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        SignatureTarget("p", "1")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        SignatureTarget("p", True)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_repository_rejects_a_non_target_and_a_bad_token():
    repo = new_repo()
    with pytest.raises(TypeError):
        await repo.get_last_signature_at(("p", 1))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        await repo.confirm(TARGET, "", confirmed_at=T0)
    with pytest.raises(TypeError):
        await repo.release(TARGET, None)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_default_tokens_are_unique_and_opaque():
    repo = MemorySignatureStateRepository()
    seen = set()
    for i in range(20):
        result = await repo.try_claim(
            SignatureTarget("p", i), now=T0, window=WINDOW, claim_ttl=TTL
        )
        assert result.claimed
        assert isinstance(result.token, str) and len(result.token) >= 16
        seen.add(result.token)
    assert len(seen) == 20
