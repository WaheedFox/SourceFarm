"""Tests for the pure signature decision (``SignaturePolicy``).

Mapping to the 11 required scenarios of the signature policy
------------------------------------------------------------
Coverage is "full" only where the policy alone decides the outcome. Scenarios that
involve batches, handlers or sending are covered ONLY at the policy level here;
their end-to-end coverage belongs to the batch/gateway part (not in this scope).

T01 private, autonomous batch, >=1 success      -> SIGN, no claim        (full)
T02 private, reply batch (e.g. to /start)       -> SIGN, no claim        (policy level: origin=REPLY; the input kind is not visible to the policy)
T03 private, reply batch (text or link)         -> SIGN, no claim        (policy level: same as T02)
T04 private, multi-message batch                -> ONE decision: SIGN    (policy level: one decision per batch; "not one per message" needs the batch layer)
T05 consecutive private batches                 -> always SIGN, the window is ignored (full)
T06 first successful group batch                -> SIGN, requires claim  (full)
T07 group batch before 24h                      -> SKIP window_active    (full)
T08 first group batch after 24h                 -> SIGN, requires claim  (full; boundary ">=" tested)
T09 same behaviour in channels                  -> as T06 to T08         (full)
T10 two bots in the same chat                   -> independent state     (covered in test_attribution_state.py)
T11 batch without successful message            -> SKIP no_successful_message (policy level; a failed batch is the batch layer's job)
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest

from hozan.features.attribution import (
    SIGNATURE_WINDOW,
    BatchOrigin,
    ChatKind,
    DecisionReason,
    EntitlementStatus,
    SignatureAction,
    SignatureDecision,
    SignatureInput,
    SignaturePolicy,
    UnknownEntitlementMode,
)

T0 = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)
SKIP_MODE = UnknownEntitlementMode.SKIP
SIGN_MODE = UnknownEntitlementMode.SIGN


def policy(mode: UnknownEntitlementMode = SKIP_MODE) -> SignaturePolicy:
    return SignaturePolicy(unknown_entitlement=mode)


def make_input(**overrides) -> SignatureInput:
    values = dict(
        entitlement=EntitlementStatus.FREE,
        chat_kind=ChatKind.PRIVATE,
        origin=BatchOrigin.REPLY,
        successful_messages=1,
        now=T0,
        last_signature_at=None,
    )
    values.update(overrides)
    return SignatureInput(**values)


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


# --------------------------------------------------------------------------
# ChatKind mapping
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "telegram_type, expected",
    [
        ("private", ChatKind.PRIVATE),
        ("group", ChatKind.GROUP),
        ("supergroup", ChatKind.GROUP),
        ("channel", ChatKind.CHANNEL),
        ("sender", ChatKind.UNKNOWN),
        ("Private", ChatKind.UNKNOWN),
        ("", ChatKind.UNKNOWN),
        (None, ChatKind.UNKNOWN),
        (5, ChatKind.UNKNOWN),
    ],
)
def test_chat_kind_from_telegram_type(telegram_type, expected):
    assert ChatKind.from_telegram_type(telegram_type) is expected


# --------------------------------------------------------------------------
# Private chats (T01, T02, T03, T04, T05)
# --------------------------------------------------------------------------


@pytest.mark.parametrize("origin", [BatchOrigin.AUTONOMOUS, BatchOrigin.REPLY])
def test_t01_t02_t03_private_batch_is_signed_for_both_origins(origin):
    decision = policy().decide(make_input(origin=origin))
    assert decision == SignatureDecision(
        SignatureAction.SIGN, DecisionReason.PRIVATE_BATCH, requires_claim=False
    )
    assert decision.should_sign


def test_t04_multi_message_private_batch_yields_a_single_decision():
    decision = policy().decide(make_input(successful_messages=5))
    assert decision.should_sign
    assert decision.reason is DecisionReason.PRIVATE_BATCH


@pytest.mark.parametrize(
    "last",
    [
        None,
        T0 - timedelta(seconds=1),
        T0 - timedelta(hours=1),
        T0 - SIGNATURE_WINDOW,
        T0 + timedelta(hours=3),  # even a future timestamp: private has no window
    ],
)
def test_t05_private_chats_ignore_the_24h_window(last):
    decision = policy().decide(make_input(last_signature_at=last))
    assert decision.should_sign
    assert decision.reason is DecisionReason.PRIVATE_BATCH
    assert decision.requires_claim is False


# --------------------------------------------------------------------------
# Groups and channels (T06, T07, T08, T09)
# --------------------------------------------------------------------------

GROUP_LIKE = [ChatKind.GROUP, ChatKind.CHANNEL]


@pytest.mark.parametrize("kind", GROUP_LIKE)
@pytest.mark.parametrize("origin", [BatchOrigin.AUTONOMOUS, BatchOrigin.REPLY])
def test_t06_t09_first_successful_batch_is_signed_and_needs_a_claim(kind, origin):
    decision = policy().decide(make_input(chat_kind=kind, origin=origin))
    assert decision == SignatureDecision(
        SignatureAction.SIGN, DecisionReason.NO_PRIOR_SIGNATURE, requires_claim=True
    )


@pytest.mark.parametrize("kind", GROUP_LIKE)
@pytest.mark.parametrize(
    "elapsed",
    [
        timedelta(0),
        timedelta(seconds=1),
        timedelta(hours=12),
        SIGNATURE_WINDOW - timedelta(microseconds=1),
    ],
)
def test_t07_t09_batch_inside_the_window_is_not_signed(kind, elapsed):
    decision = policy().decide(
        make_input(chat_kind=kind, last_signature_at=T0 - elapsed)
    )
    assert decision == SignatureDecision(
        SignatureAction.SKIP, DecisionReason.WINDOW_ACTIVE
    )


@pytest.mark.parametrize("kind", GROUP_LIKE)
@pytest.mark.parametrize(
    "elapsed",
    [
        SIGNATURE_WINDOW,  # exactly 24h counts as elapsed (>=)
        SIGNATURE_WINDOW + timedelta(microseconds=1),
        SIGNATURE_WINDOW + timedelta(hours=5),
        timedelta(days=30),
    ],
)
def test_t08_t09_first_batch_after_the_window_is_signed(kind, elapsed):
    decision = policy().decide(
        make_input(chat_kind=kind, last_signature_at=T0 - elapsed)
    )
    assert decision == SignatureDecision(
        SignatureAction.SIGN, DecisionReason.WINDOW_ELAPSED, requires_claim=True
    )


@pytest.mark.parametrize("origin", [BatchOrigin.AUTONOMOUS, BatchOrigin.REPLY])
def test_group_rule_does_not_depend_on_origin(origin):
    inside = policy().decide(
        make_input(
            chat_kind=ChatKind.GROUP,
            origin=origin,
            last_signature_at=T0 - timedelta(hours=1),
        )
    )
    assert inside.reason is DecisionReason.WINDOW_ACTIVE


def test_custom_window_is_respected():
    short = SignaturePolicy(unknown_entitlement=SKIP_MODE, window=timedelta(hours=1))
    assert short.window == timedelta(hours=1)
    decision = short.decide(
        make_input(chat_kind=ChatKind.GROUP, last_signature_at=T0 - timedelta(hours=1))
    )
    assert decision.reason is DecisionReason.WINDOW_ELAPSED


# --------------------------------------------------------------------------
# Future last_signature_at: explicit, testable, logged, no state involved
# --------------------------------------------------------------------------


@pytest.mark.parametrize("kind", GROUP_LIKE)
def test_future_last_signature_is_an_explicit_skip_and_is_logged(kind):
    last = T0 + timedelta(minutes=5)
    with captured_warnings() as records:
        decision = policy().decide(make_input(chat_kind=kind, last_signature_at=last))
    assert decision == SignatureDecision(
        SignatureAction.SKIP, DecisionReason.LAST_SIGNATURE_IN_FUTURE
    )
    assert len(records) == 1
    assert "future" in records[0].getMessage()
    assert last.isoformat() in records[0].getMessage()


def test_future_last_signature_one_microsecond_ahead_is_still_future():
    with captured_warnings() as records:
        decision = policy().decide(
            make_input(
                chat_kind=ChatKind.GROUP, last_signature_at=T0 + timedelta(microseconds=1)
            )
        )
    assert decision.reason is DecisionReason.LAST_SIGNATURE_IN_FUTURE
    assert len(records) == 1


def test_last_signature_equal_to_now_is_inside_the_window_not_future():
    with captured_warnings() as records:
        decision = policy().decide(
            make_input(chat_kind=ChatKind.GROUP, last_signature_at=T0)
        )
    assert decision.reason is DecisionReason.WINDOW_ACTIVE
    assert records == []


# --------------------------------------------------------------------------
# No successful message (T11), plan, unknown kinds
# --------------------------------------------------------------------------


@pytest.mark.parametrize("kind", [ChatKind.PRIVATE, ChatKind.GROUP, ChatKind.CHANNEL])
@pytest.mark.parametrize("origin", [BatchOrigin.AUTONOMOUS, BatchOrigin.REPLY])
def test_t11_no_successful_message_never_produces_a_signature(kind, origin):
    decision = policy().decide(
        make_input(chat_kind=kind, origin=origin, successful_messages=0)
    )
    assert decision == SignatureDecision(
        SignatureAction.SKIP, DecisionReason.NO_SUCCESSFUL_MESSAGE
    )


@pytest.mark.parametrize("kind", [ChatKind.PRIVATE, ChatKind.GROUP, ChatKind.CHANNEL])
def test_paid_plans_are_never_signed(kind):
    decision = policy().decide(make_input(chat_kind=kind, entitlement=EntitlementStatus.PAID))
    assert decision == SignatureDecision(
        SignatureAction.SKIP, DecisionReason.NOT_FREE_PLAN
    )


@pytest.mark.parametrize("entitlement", list(EntitlementStatus))
@pytest.mark.parametrize("origin", [BatchOrigin.AUTONOMOUS, BatchOrigin.REPLY])
def test_unknown_chat_kind_never_produces_a_signature(entitlement, origin):
    decision = policy(SIGN_MODE).decide(
        make_input(chat_kind=ChatKind.UNKNOWN, entitlement=entitlement, origin=origin)
    )
    if entitlement is EntitlementStatus.PAID:
        assert decision.reason is DecisionReason.NOT_FREE_PLAN
    else:
        assert decision == SignatureDecision(
            SignatureAction.SKIP, DecisionReason.CHAT_KIND_UNKNOWN
        )


def test_unknown_entitlement_in_skip_mode_is_not_signed():
    decision = policy(SKIP_MODE).decide(
        make_input(entitlement=EntitlementStatus.UNKNOWN)
    )
    assert decision == SignatureDecision(
        SignatureAction.SKIP, DecisionReason.ENTITLEMENT_UNKNOWN
    )


def test_unknown_entitlement_in_sign_mode_continues_with_the_other_rules():
    private = policy(SIGN_MODE).decide(
        make_input(entitlement=EntitlementStatus.UNKNOWN)
    )
    assert private.should_sign
    group_inside = policy(SIGN_MODE).decide(
        make_input(
            entitlement=EntitlementStatus.UNKNOWN,
            chat_kind=ChatKind.GROUP,
            last_signature_at=T0 - timedelta(hours=1),
        )
    )
    assert group_inside.reason is DecisionReason.WINDOW_ACTIVE


def test_rule_order_is_fixed_no_message_wins_over_everything():
    decision = policy().decide(
        make_input(
            successful_messages=0,
            entitlement=EntitlementStatus.PAID,
            chat_kind=ChatKind.UNKNOWN,
        )
    )
    assert decision.reason is DecisionReason.NO_SUCCESSFUL_MESSAGE


def test_rule_order_is_fixed_plan_wins_over_chat_kind():
    decision = policy().decide(
        make_input(entitlement=EntitlementStatus.PAID, chat_kind=ChatKind.UNKNOWN)
    )
    assert decision.reason is DecisionReason.NOT_FREE_PLAN


# --------------------------------------------------------------------------
# Open decision D8 stays explicit; invalid values are rejected, not converted
# --------------------------------------------------------------------------


def test_unknown_entitlement_mode_is_required_there_is_no_default():
    with pytest.raises(TypeError):
        SignaturePolicy()  # type: ignore[call-arg]


def test_unknown_entitlement_mode_must_be_the_enum():
    with pytest.raises(TypeError):
        SignaturePolicy(unknown_entitlement="skip")  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [timedelta(0), timedelta(hours=-1)])
def test_window_must_be_positive(bad):
    with pytest.raises(ValueError):
        SignaturePolicy(unknown_entitlement=SKIP_MODE, window=bad)


def test_window_must_be_a_timedelta():
    with pytest.raises(TypeError):
        SignaturePolicy(unknown_entitlement=SKIP_MODE, window=24)  # type: ignore[arg-type]


def test_naive_datetime_is_rejected_not_converted():
    with pytest.raises(ValueError, match="timezone-aware"):
        make_input(now=datetime(2026, 11, 15, 12, 0))


def test_naive_last_signature_is_rejected_not_converted():
    with pytest.raises(ValueError, match="timezone-aware"):
        make_input(last_signature_at=datetime(2026, 11, 14, 12, 0))


def test_non_utc_offset_is_rejected_not_converted():
    plus_three = timezone(timedelta(hours=3))
    with pytest.raises(ValueError, match="UTC"):
        make_input(now=datetime(2026, 11, 15, 15, 0, tzinfo=plus_three))
    with pytest.raises(ValueError, match="UTC"):
        make_input(last_signature_at=datetime(2026, 11, 14, 15, 0, tzinfo=plus_three))


@pytest.mark.parametrize("bad", ["2026-11-15", 1_700_000_000, None])
def test_non_datetime_now_is_rejected(bad):
    with pytest.raises(TypeError):
        make_input(now=bad)


@pytest.mark.parametrize("bad", [-1])
def test_negative_successful_messages_are_rejected(bad):
    with pytest.raises(ValueError):
        make_input(successful_messages=bad)


@pytest.mark.parametrize("bad", [True, 1.0, "1", None])
def test_successful_messages_must_be_a_real_int(bad):
    with pytest.raises(TypeError):
        make_input(successful_messages=bad)


@pytest.mark.parametrize(
    "field, bad",
    [
        ("entitlement", "free"),
        ("chat_kind", "private"),
        ("origin", "reply"),
    ],
)
def test_enum_fields_reject_plain_strings(field, bad):
    with pytest.raises(TypeError):
        make_input(**{field: bad})


def test_decide_rejects_a_non_input():
    with pytest.raises(TypeError):
        policy().decide({"chat_kind": "private"})  # type: ignore[arg-type]


def test_decision_object_rejects_inconsistent_action_and_reason():
    with pytest.raises(ValueError):
        SignatureDecision(SignatureAction.SIGN, DecisionReason.WINDOW_ACTIVE)
    with pytest.raises(ValueError):
        SignatureDecision(SignatureAction.SKIP, DecisionReason.PRIVATE_BATCH)
    with pytest.raises(ValueError):
        SignatureDecision(
            SignatureAction.SKIP, DecisionReason.WINDOW_ACTIVE, requires_claim=True
        )


def test_policy_does_not_mutate_or_depend_on_hidden_state():
    inp = make_input(chat_kind=ChatKind.GROUP, last_signature_at=T0 - timedelta(hours=30))
    first = policy().decide(inp)
    second = policy().decide(inp)
    assert first == second
