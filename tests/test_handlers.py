"""Tests for handler utilities with mocked integrations."""
from __future__ import annotations

import pytest

from utils.auth import MusicKitConfig
from utils.exceptions import ToolError


@pytest.fixture
def config() -> MusicKitConfig:
    return MusicKitConfig(
        team_id="TEAM",
        key_id="KEY",
        private_key_path="/tmp/key",
        storefront="us",
    )


def test_search_handler_caching(monkeypatch, config):
    from handlers import search as search_handler

    monkeypatch.setattr(search_handler, "load_config", lambda: config)
    search_handler._SEARCH_CACHE.clear()

    calls = {"count": 0}

    def fake_search_catalog(**kwargs):
        calls["count"] += 1
        return {
            "results": {
                "songs": {
                    "data": [
                        {
                            "id": "1",
                            "type": "songs",
                            "attributes": {
                                "name": "Song",
                                "artistName": "Artist",
                                "albumName": "Album",
                                "url": "https://example.test",
                            },
                        }
                    ]
                }
            }
        }

    monkeypatch.setattr(search_handler.musickit, "search_catalog", fake_search_catalog)

    first = search_handler.handle_search({"term": "hello"})
    assert first["source"] == "live"
    second = search_handler.handle_search({"term": "hello"})
    assert second["source"] == "cache"
    assert calls["count"] == 1


def test_play_song_invokes_applescript(monkeypatch, config):
    from handlers import play as play_handler

    monkeypatch.setattr(play_handler, "load_config", lambda: config)
    monkeypatch.setattr(
        play_handler.musickit,
        "get_song",
        lambda config, song_id: {
            "id": song_id,
            "name": "Song",
            "artist": "Artist",
            "album": "Album",
            "url": "https://example.test",
            "play_params": {},
        },
    )

    captured = {}

    def fake_applescript(script: str) -> None:
        captured["script"] = script

    monkeypatch.setattr(play_handler, "run_applescript", fake_applescript)

    response = play_handler.handle_play_song({"track_id": "1"})
    assert response["status"] == "playing"
    assert "Music" in captured["script"]


def test_playback_argument_validation():
    from handlers import playback as playback_handler

    with pytest.raises(ToolError):
        playback_handler.handle_playback_control({"action": "invalid"})
