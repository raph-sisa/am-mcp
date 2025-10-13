"""Tests for MusicKit authentication helpers."""
from __future__ import annotations

import pytest

from utils.auth import generate_developer_token, load_config
from utils.exceptions import ToolError


TEST_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----\nMIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgrWfyj2sExtjSN+XX\ntdKLAQm3yAMuQ7v8h/UlPrj26r+hRANCAAQ/bG6h9Ldp9LmQcqmokqMD9iHiYQc3\n8jgfqKtX6vRKCrP0fsYmGeGAg724fw1kWYUenCz0dypFafvtgX1DVLkn\n-----END PRIVATE KEY-----\n"""


@pytest.fixture(autouse=True)
def configure_env(tmp_path, monkeypatch):
    key_path = tmp_path / "AuthKey_TEST.p8"
    key_path.write_text(TEST_PRIVATE_KEY)
    monkeypatch.setenv("TEAM_ID", "TEAM1234")
    monkeypatch.setenv("KEY_ID", "KEY1234")
    monkeypatch.setenv("PRIVATE_KEY_PATH", str(key_path))
    monkeypatch.setenv("STOREFRONT", "us")
    yield


def test_generate_developer_token(monkeypatch):
    config = load_config()
    token = generate_developer_token(config, ttl_seconds=600)
    _, payload_b64, _ = token.split(".")
    payload = _decode_segment(payload_b64)
    assert payload["iss"] == "TEAM1234"
    assert payload["aud"] == "https://music.apple.com"
    assert payload["exp"] - payload["iat"] <= 600


def test_token_cache(monkeypatch):
    config = load_config()
    token1 = generate_developer_token(config, ttl_seconds=600)
    token2 = generate_developer_token(config, ttl_seconds=600)
    assert token1 == token2


def test_ttl_bounds(monkeypatch):
    config = load_config()
    with pytest.raises(ToolError):
        generate_developer_token(config, ttl_seconds=0)
    with pytest.raises(ToolError):
        generate_developer_token(config, ttl_seconds=60 * 60 * 24 * 181)


def _decode_segment(segment: str) -> dict:
    import base64
    import json

    padding = "=" * (-len(segment) % 4)
    data = base64.urlsafe_b64decode(segment + padding)
    return json.loads(data.decode("utf-8"))
