"""The signature message: fixed text, one ``text_link`` entity, silent send.

Decided: the visible text is exactly ``Powered by SourceFarm``; only the word
``SourceFarm`` is a link (a ``text_link`` entity, no buttons, no shorteners); the
message is sent silently (``disable_notification=True``).

Kept OUT (open decisions, no behavior invented):
* D10: the URL. ``build_signature_message`` requires it as an argument; this module
  contains no URL constant.
* D6: link preview. It is an optional flag; unset means the parameter is omitted.

Not verified here (no network): the exact Bot API name ``link_preview_options``
(Bot API 7.0 per the author's knowledge). The later sender part must verify it.

Entity offsets and lengths are measured in UTF-16 code units, as Telegram requires.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

SIGNATURE_TEXT = "Powered by SourceFarm"
SIGNATURE_LINK_WORD = "SourceFarm"


def _utf16_length(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


@dataclass(frozen=True, slots=True)
class TextLinkEntity:
    offset: int
    length: int
    url: str

    def to_bot_api(self) -> dict[str, Any]:
        return {
            "type": "text_link",
            "offset": self.offset,
            "length": self.length,
            "url": self.url,
        }


@dataclass(frozen=True, slots=True)
class SignatureMessage:
    text: str
    entities: tuple[TextLinkEntity, ...]
    disable_notification: bool = True
    link_preview_disabled: bool | None = None

    def to_send_message_params(self) -> dict[str, Any]:
        """``sendMessage`` parameters WITHOUT ``chat_id`` (added by the sender)."""
        params: dict[str, Any] = {
            "text": self.text,
            "entities": [entity.to_bot_api() for entity in self.entities],
            "disable_notification": self.disable_notification,
        }
        if self.link_preview_disabled is not None:
            params["link_preview_options"] = {"is_disabled": self.link_preview_disabled}
        return params


def _check_url(url: object) -> str:
    if not isinstance(url, str):
        raise TypeError("url must be a str")
    if not url or any(ch.isspace() for ch in url):
        raise ValueError("url must be non-empty and contain no whitespace")
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise ValueError("url must be an absolute http(s) URL")
    return url


def build_signature_message(
    url: str,
    *,
    link_preview_disabled: bool | None = None,
) -> SignatureMessage:
    _check_url(url)
    if link_preview_disabled is not None and not isinstance(link_preview_disabled, bool):
        raise TypeError("link_preview_disabled must be a bool or None")
    start = SIGNATURE_TEXT.index(SIGNATURE_LINK_WORD)
    entity = TextLinkEntity(
        offset=_utf16_length(SIGNATURE_TEXT[:start]),
        length=_utf16_length(SIGNATURE_LINK_WORD),
        url=url,
    )
    return SignatureMessage(
        text=SIGNATURE_TEXT,
        entities=(entity,),
        disable_notification=True,
        link_preview_disabled=link_preview_disabled,
    )
