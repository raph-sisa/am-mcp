"""Play handler implementation."""
from __future__ import annotations

from typing import Any, Dict, Optional

from utils import musickit
from utils.apple_script import run_applescript
from utils.auth import load_config
from utils.exceptions import ToolError


def _fetch_track(track_id: str) -> Dict[str, Any]:
    config = load_config()
    return musickit.get_song(config=config, song_id=track_id)


def _build_play_script(url: str) -> str:
    safe_url = url.replace("\"", "\\\"")
    return f'''
set musicApp to application "Music"
if not running of musicApp then
    launch musicApp
end if
delay 0.2
open location "{safe_url}"
delay 0.5
tell application "Music" to play
'''


def _parse_arguments(arguments: Dict[str, Any]) -> Dict[str, Optional[str]]:
    if not isinstance(arguments, dict):
        raise ToolError("invalid_arguments", "Arguments for play_song must be an object.")

    unexpected = set(arguments.keys()) - {"track_id", "play_location_url"}
    if unexpected:
        raise ToolError(
            "invalid_arguments",
            "Unexpected parameters provided to play_song.",
            f"Unsupported keys: {', '.join(sorted(unexpected))}.",
        )

    track_id = arguments.get("track_id")
    if not isinstance(track_id, str) or not track_id:
        raise ToolError(
            "invalid_arguments",
            "'track_id' is required and must be a string.",
        )

    play_location_url = arguments.get("play_location_url")
    if play_location_url is not None and not isinstance(play_location_url, str):
        raise ToolError(
            "invalid_arguments",
            "'play_location_url' must be a string when provided.",
        )

    return {"track_id": track_id, "play_location_url": play_location_url}


def handle_play_song(arguments: Dict[str, Any]) -> Dict[str, Any]:
    args = _parse_arguments(arguments)

    track = _fetch_track(args["track_id"])
    url = args["play_location_url"] or track.get("url")

    if not url:
        play_params = track.get("play_params") or {}
        catalog_id = play_params.get("catalogId") or play_params.get("id")
        if catalog_id:
            url = f"https://music.apple.com/{catalog_id}"

    if not url:
        raise ToolError(
            "playback_url_unavailable",
            "No playable URL was available for the requested track.",
            "Ensure the track is available in the configured storefront.",
        )

    run_applescript(_build_play_script(url))

    return {
        "status": "playing",
        "track": track,
        "play_location_url": url,
    }
