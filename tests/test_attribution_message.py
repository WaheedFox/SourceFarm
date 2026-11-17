"""Tests for the signature message (text, entity, silent flag, URL handling).

The URL is deliberately a test-local placeholder: the real destination/link is an
open decision (D10) and is not defined in the code under test.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from hozan.features.attribution import (
    SIGNATURE_LINK_WORD,
    SIGNATURE_TEXT,
    build_signature_message,
)
from hozan.features.attribution.message import _utf16_length

TEST_URL = "https://example.test/placeholder?x=1"


def test_visible_text_is_exactly_the_approved_text():
    message = build_signature_message(TEST_URL)
    assert message.text == "Powered by SourceFarm"
    assert SIGNATURE_TEXT == "Powered by SourceFarm"
    assert SIGNATURE_LINK_WORD == "SourceFarm"


def test_only_the_word_sourcefarm_is_a_text_link_entity():
    message = build_signature_message(TEST_URL)
    assert len(message.entities) == 1
    entity = message.entities[0]
    assert (entity.offset, entity.length) == (11, 10)
    assert message.text[entity.offset : entity.offset + entity.length] == "SourceFarm"
    assert entity.url == TEST_URL
    assert entity.to_bot_api() == {
        "type": "text_link",
        "offset": 11,
        "length": 10,
        "url": TEST_URL,
    }


def test_message_is_silent():
    message = build_signature_message(TEST_URL)
    assert message.disable_notification is True
    assert message.to_send_message_params()["disable_notification"] is True


def test_params_have_no_chat_id_and_no_reply_markup_and_no_buttons():
    params = build_signature_message(TEST_URL).to_send_message_params()
    assert set(params) == {"text", "entities", "disable_notification"}
    assert "reply_markup" not in params
    assert "chat_id" not in params


def test_link_preview_is_omitted_when_unset():
    message = build_signature_message(TEST_URL)
    assert message.link_preview_disabled is None
    assert "link_preview_options" not in message.to_send_message_params()


@pytest.mark.parametrize("flag", [True, False])
def test_link_preview_flag_is_passed_through_when_set(flag):
    params = build_signature_message(
        TEST_URL, link_preview_disabled=flag
    ).to_send_message_params()
    assert params["link_preview_options"] == {"is_disabled": flag}


def test_link_preview_flag_must_be_a_bool_or_none():
    with pytest.raises(TypeError):
        build_signature_message(TEST_URL, link_preview_disabled="yes")  # type: ignore[arg-type]


def test_params_are_json_serializable():
    params = build_signature_message(TEST_URL, link_preview_disabled=True).to_send_message_params()
    assert json.loads(json.dumps(params)) == params


def test_url_is_required_the_module_has_no_default_destination():
    with pytest.raises(TypeError):
        build_signature_message()  # type: ignore[call-arg]


@pytest.mark.parametrize(
    "bad",
    ["", " ", "https://exa mple.test", "example.test", "ftp://example.test/x", "https://", "t.me/x"],
)
def test_invalid_urls_are_rejected(bad):
    with pytest.raises(ValueError):
        build_signature_message(bad)


@pytest.mark.parametrize("bad", [None, 5, b"https://example.test"])
def test_non_str_urls_are_rejected(bad):
    with pytest.raises(TypeError):
        build_signature_message(bad)  # type: ignore[arg-type]


def test_the_url_is_not_altered():
    url = "https://example.test/a?b=c&d=e#frag"
    assert build_signature_message(url).entities[0].url == url


def test_message_objects_are_immutable():
    message = build_signature_message(TEST_URL)
    with pytest.raises(dataclasses.FrozenInstanceError):
        message.text = "other"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        message.entities[0].url = "https://other.test"  # type: ignore[misc]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", 0),
        ("abc", 3),
        ("Powered by ", 11),
        ("é", 1),
        ("\U0001F600", 2),  # one code point, two UTF-16 code units
        ("a\U0001F600b", 4),
    ],
)
def test_utf16_length_counts_code_units_as_telegram_does(text, expected):
    assert _utf16_length(text) == expected
