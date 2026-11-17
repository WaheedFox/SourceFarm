"""Pure decision function: should this batch be followed by a signature?

Decided rules implemented here
------------------------------
1. A batch with no successful message never produces a signature.
2. Only the free plan is signed. ``PAID`` is never signed.
3. An unknown chat kind never produces a signature.
4. Private chats: every qualifying batch is signed, whether it was an autonomous
   send or a reply to a user interaction. There is no waiting period.
5. Groups and channels: the 24-hour rule only. One signature, then none until
   ``window`` has elapsed since the previous signature was CONFIRMED; the next
   qualifying batch after that is signed. ``origin`` is irrelevant.

Open decisions kept OUT of this module
--------------------------------------
* D8 (unknown entitlement): ``unknown_entitlement`` is required, no default.
* D2 (what is a successful message) and D14 (what is a batch): the policy receives
  ``successful_messages`` already computed.

Nothing here reads a clock, touches storage or sends anything.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from .models import (
    SIGNATURE_WINDOW,
    ChatKind,
    DecisionReason,
    EntitlementStatus,
    SignatureAction,
    SignatureDecision,
    SignatureInput,
    UnknownEntitlementMode,
    WindowState,
    ensure_positive_timedelta,
    evaluate_window,
)

logger = logging.getLogger(__name__)


def _skip(reason: DecisionReason) -> SignatureDecision:
    return SignatureDecision(SignatureAction.SKIP, reason)


class SignaturePolicy:
    def __init__(
        self,
        *,
        unknown_entitlement: UnknownEntitlementMode,
        window: timedelta = SIGNATURE_WINDOW,
    ) -> None:
        if not isinstance(unknown_entitlement, UnknownEntitlementMode):
            raise TypeError("unknown_entitlement must be an UnknownEntitlementMode")
        self._unknown_entitlement = unknown_entitlement
        self._window = ensure_positive_timedelta(window, "window")

    @property
    def window(self) -> timedelta:
        return self._window

    def decide(self, inp: SignatureInput) -> SignatureDecision:
        """Rules are evaluated in this fixed order; the first match wins."""
        if not isinstance(inp, SignatureInput):
            raise TypeError("inp must be a SignatureInput")

        if inp.successful_messages == 0:
            return _skip(DecisionReason.NO_SUCCESSFUL_MESSAGE)

        if inp.entitlement is EntitlementStatus.PAID:
            return _skip(DecisionReason.NOT_FREE_PLAN)
        if (
            inp.entitlement is EntitlementStatus.UNKNOWN
            and self._unknown_entitlement is UnknownEntitlementMode.SKIP
        ):
            return _skip(DecisionReason.ENTITLEMENT_UNKNOWN)

        if inp.chat_kind is ChatKind.UNKNOWN:
            return _skip(DecisionReason.CHAT_KIND_UNKNOWN)

        if inp.chat_kind is ChatKind.PRIVATE:
            # No state and no window for private chats, for either origin.
            return SignatureDecision(SignatureAction.SIGN, DecisionReason.PRIVATE_BATCH)

        # Group or channel: the 24-hour window only.
        state = evaluate_window(
            last_signature_at=inp.last_signature_at,
            now=inp.now,
            window=self._window,
        )
        if state is WindowState.FUTURE:
            logger.warning(
                "signature skipped: last_signature_at is in the future "
                "(now=%s, last_signature_at=%s); state is not modified",
                inp.now.isoformat(),
                inp.last_signature_at.isoformat() if inp.last_signature_at else None,
            )
            return _skip(DecisionReason.LAST_SIGNATURE_IN_FUTURE)
        if state is WindowState.ACTIVE:
            return _skip(DecisionReason.WINDOW_ACTIVE)

        reason = (
            DecisionReason.NO_PRIOR_SIGNATURE
            if inp.last_signature_at is None
            else DecisionReason.WINDOW_ELAPSED
        )
        return SignatureDecision(SignatureAction.SIGN, reason, requires_claim=True)
