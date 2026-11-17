"""Value objects for the attribution signature decision core.

Scope: pure data and pure functions. No I/O, no Titan, no CUPS, no database.

Terminology
-----------
* "signature": the standalone "Powered by SourceFarm" message (see ``message.py``).
* "batch": one group of outgoing messages. How a batch is delimited is an OPEN
  decision (D14) and is intentionally *not* modelled here: the policy receives the
  number of successful messages of an already-delimited batch.
* "successful message": what counts as one is an OPEN decision (D2) and is
  intentionally *not* decided here, for the same reason.

All datetimes handled by this package must be timezone-aware and in UTC
(offset zero). Anything else is rejected with an error; it is never converted
silently.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

# Decided: groups and channels may receive at most one signature per this window,
# measured from the time the previous signature was *confirmed*.
SIGNATURE_WINDOW = timedelta(hours=24)


class ChatKind(str, Enum):
    PRIVATE = "private"
    GROUP = "group"
    CHANNEL = "channel"
    UNKNOWN = "unknown"

    @classmethod
    def from_telegram_type(cls, value: object) -> ChatKind:
        """Map a Telegram ``chat.type`` string to a ``ChatKind``.

        ``supergroup`` is a group for this policy. Anything that is not exactly one
        of the known strings (including ``None``) maps to ``UNKNOWN``, which means
        "no signature" (decided).
        """
        if not isinstance(value, str):
            return cls.UNKNOWN
        return _TELEGRAM_CHAT_TYPES.get(value, cls.UNKNOWN)


_TELEGRAM_CHAT_TYPES: dict[str, ChatKind] = {
    "private": ChatKind.PRIVATE,
    "group": ChatKind.GROUP,
    "supergroup": ChatKind.GROUP,
    "channel": ChatKind.CHANNEL,
}


class BatchOrigin(str, Enum):
    """Why a batch was sent. The decided private-chat rule treats both alike."""

    REPLY = "reply"
    AUTONOMOUS = "autonomous"


class EntitlementStatus(str, Enum):
    FREE = "free"
    PAID = "paid"
    UNKNOWN = "unknown"


class UnknownEntitlementMode(str, Enum):
    """How ``EntitlementStatus.UNKNOWN`` is treated.

    This is an OPEN decision (D8). Both outcomes are representable so that the
    choice can be made later without changing the policy; callers must pass it
    explicitly and there is deliberately no default.
    """

    SKIP = "skip"
    SIGN = "sign"


class SignatureAction(str, Enum):
    SIGN = "sign"
    SKIP = "skip"


class DecisionReason(str, Enum):
    # reasons that go with SignatureAction.SIGN
    PRIVATE_BATCH = "private_batch"
    NO_PRIOR_SIGNATURE = "no_prior_signature"
    WINDOW_ELAPSED = "window_elapsed"
    # reasons that go with SignatureAction.SKIP
    NO_SUCCESSFUL_MESSAGE = "no_successful_message"
    NOT_FREE_PLAN = "not_free_plan"
    ENTITLEMENT_UNKNOWN = "entitlement_unknown"
    CHAT_KIND_UNKNOWN = "chat_kind_unknown"
    WINDOW_ACTIVE = "window_active"
    LAST_SIGNATURE_IN_FUTURE = "last_signature_in_future"


SIGN_REASONS = frozenset(
    {
        DecisionReason.PRIVATE_BATCH,
        DecisionReason.NO_PRIOR_SIGNATURE,
        DecisionReason.WINDOW_ELAPSED,
    }
)
SKIP_REASONS = frozenset(set(DecisionReason) - SIGN_REASONS)


class WindowState(str, Enum):
    OPEN = "open"
    ACTIVE = "active"
    FUTURE = "future"


def ensure_utc(value: object, name: str) -> datetime:
    """Return ``value`` if it is a timezone-aware UTC datetime, else raise.

    Naive datetimes and datetimes with a non-zero UTC offset are rejected, never
    converted.
    """
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime, got {type(value).__name__}")
    offset = value.utcoffset()
    if value.tzinfo is None or offset is None:
        raise ValueError(
            f"{name} must be timezone-aware (UTC); naive datetimes are rejected, "
            "not converted"
        )
    if offset != timedelta(0):
        raise ValueError(
            f"{name} must be in UTC (offset 0), got offset {offset}; "
            "it is rejected, not converted"
        )
    return value


def ensure_positive_timedelta(value: object, name: str) -> timedelta:
    if not isinstance(value, timedelta):
        raise TypeError(f"{name} must be a timedelta, got {type(value).__name__}")
    if value <= timedelta(0):
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def evaluate_window(
    *,
    last_signature_at: datetime | None,
    now: datetime,
    window: timedelta,
) -> WindowState:
    """Single source of truth for the 24-hour window rule.

    * no previous signature            -> ``OPEN``
    * ``last`` is later than ``now``   -> ``FUTURE`` (explicit state, never "open")
    * ``now - last >= window``         -> ``OPEN``  (exactly ``window`` has elapsed)
    * otherwise                        -> ``ACTIVE``

    ``last_signature_at`` is the time the previous signature was CONFIRMED as sent;
    it is never the time of a claim or of a send attempt.
    """
    ensure_utc(now, "now")
    ensure_positive_timedelta(window, "window")
    if last_signature_at is None:
        return WindowState.OPEN
    ensure_utc(last_signature_at, "last_signature_at")
    if last_signature_at > now:
        return WindowState.FUTURE
    if now - last_signature_at >= window:
        return WindowState.OPEN
    return WindowState.ACTIVE


@dataclass(frozen=True, slots=True)
class SignatureTarget:
    """Key of the signature state: independent per (project, chat)."""

    project_id: str
    chat_id: int

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str):
            raise TypeError("project_id must be a str")
        if not self.project_id.strip():
            raise ValueError("project_id must not be blank")
        if isinstance(self.chat_id, bool) or not isinstance(self.chat_id, int):
            raise TypeError("chat_id must be an int")


@dataclass(frozen=True, slots=True)
class SignatureInput:
    """Everything the policy needs to decide about ONE batch."""

    entitlement: EntitlementStatus
    chat_kind: ChatKind
    origin: BatchOrigin
    successful_messages: int
    now: datetime
    last_signature_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.entitlement, EntitlementStatus):
            raise TypeError("entitlement must be an EntitlementStatus")
        if not isinstance(self.chat_kind, ChatKind):
            raise TypeError("chat_kind must be a ChatKind")
        if not isinstance(self.origin, BatchOrigin):
            raise TypeError("origin must be a BatchOrigin")
        if isinstance(self.successful_messages, bool) or not isinstance(
            self.successful_messages, int
        ):
            raise TypeError("successful_messages must be an int")
        if self.successful_messages < 0:
            raise ValueError("successful_messages must not be negative")
        ensure_utc(self.now, "now")
        if self.last_signature_at is not None:
            ensure_utc(self.last_signature_at, "last_signature_at")


@dataclass(frozen=True, slots=True)
class SignatureDecision:
    action: SignatureAction
    reason: DecisionReason
    # True when the caller must win ``SignatureStateRepository.try_claim`` before
    # sending (groups and channels). The policy decides on a snapshot; the claim is
    # what makes the decision safe under concurrency.
    requires_claim: bool = False

    def __post_init__(self) -> None:
        if self.action is SignatureAction.SIGN and self.reason not in SIGN_REASONS:
            raise ValueError(f"reason {self.reason.value} is not a SIGN reason")
        if self.action is SignatureAction.SKIP and self.reason not in SKIP_REASONS:
            raise ValueError(f"reason {self.reason.value} is not a SKIP reason")
        if self.action is SignatureAction.SKIP and self.requires_claim:
            raise ValueError("a SKIP decision cannot require a claim")

    @property
    def should_sign(self) -> bool:
        return self.action is SignatureAction.SIGN
